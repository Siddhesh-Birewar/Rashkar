"""
Private Supabase Storage Service with Local Filesystem Fallback.

Provides:
- Private bucket management for `soil-reports` (public: false)
- Structured storage path generation: `{farm_id}/{report_id}/{safe_filename}`
- Time-limited HMAC signed URL generation via Supabase Storage REST API
- Deterministic local filesystem storage fallback (`data_cache/soil_reports/`)
  for offline, containerized, and mock test environments
- Absolute prevention of public storage URL exposure
"""
import os
import re
import logging
from pathlib import Path
from typing import Optional, Tuple
import httpx

try:
    from cropnet.services.api.app.core.config import settings
except ImportError:
    from ..core.config import settings

logger = logging.getLogger(__name__)

BUCKET_NAME = "soil-reports"
LOCAL_FALLBACK_BASE_DIR = Path("data_cache/soil_reports")


class SoilReportStorageService:
    """
    Manages private document storage and signed URL retrieval for soil lab reports.
    """

    def __init__(self):
        self.bucket = BUCKET_NAME
        self.supabase_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else None
        self.service_key = settings.SUPABASE_SECRET_KEY
        self.local_dir = LOCAL_FALLBACK_BASE_DIR
        self._ensure_local_dir()

    def _ensure_local_dir(self) -> None:
        """Ensure local storage cache directory exists."""
        try:
            self.local_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning("Could not create local storage fallback directory: %s", e)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize user filename to eliminate path traversal, non-printable characters,
        and unsafe punctuation.
        """
        # Strip directory paths
        base = os.path.basename(filename)
        # Retain only alphanumeric, dots, underscores, hyphens
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
        # Avoid hidden files
        if sanitized.startswith("."):
            sanitized = "doc" + sanitized
        return sanitized or "document.pdf"

    def ensure_bucket_exists(self) -> bool:
        """
        Verify or create the private Supabase storage bucket `soil-reports`.
        Returns True if bucket is available, False if offline/unavailable.
        """
        if not self.supabase_url or not self.service_key:
            return False

        try:
            url = f"{self.supabase_url}/storage/v1/bucket/{self.bucket}"
            headers = {
                "Authorization": f"Bearer {self.service_key}",
                "apikey": self.service_key,
            }
            with httpx.Client(timeout=5.0) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    return True
                elif res.status_code == 404:
                    # Create private bucket
                    create_url = f"{self.supabase_url}/storage/v1/bucket"
                    payload = {
                        "id": self.bucket,
                        "name": self.bucket,
                        "public": False,
                        "file_size_limit": 15728640,  # 15MB
                        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
                    }
                    create_res = client.post(create_url, headers=headers, json=payload)
                    return create_res.status_code in (200, 201)
        except Exception as e:
            logger.info("Supabase storage bucket verification skipped / offline: %s", e)
        return False

    def upload_file(
        self,
        farm_id: str,
        report_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/pdf"
    ) -> str:
        """
        Upload file to private storage with path `{farm_id}/{report_id}/{safe_filename}`.
        Always saves to local fallback cache and attempts Supabase cloud storage if online.
        Returns the structured storage path.
        """
        safe_name = self.sanitize_filename(filename)
        storage_path = f"{farm_id}/{report_id}/{safe_name}"

        # 1. Always persist to local fallback cache
        local_file_path = self.local_dir / storage_path
        local_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_file_path, "wb") as f:
            f.write(content)

        # 2. Upload to remote Supabase private bucket if configured
        if self.supabase_url and self.service_key:
            try:
                upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
                headers = {
                    "Authorization": f"Bearer {self.service_key}",
                    "apikey": self.service_key,
                    "Content-Type": content_type,
                    "x-upsert": "true",
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(upload_url, headers=headers, content=content)
                    if resp.status_code not in (200, 201):
                        logger.warning(
                            "Supabase storage upload returned status %s for %s, falling back to local storage: %s",
                            resp.status_code, storage_path, resp.text
                        )
            except Exception as e:
                logger.info("Supabase storage upload offline/skipped: %s. Local fallback active.", e)

        return storage_path

    def generate_signed_url(
        self,
        storage_path: str,
        farm_id: Optional[str] = None,
        report_id: Optional[str] = None,
        expires_in_seconds: int = 3600
    ) -> str:
        """
        Generate a time-limited signed URL for private document download.
        If live Supabase Storage is reachable, uses POST /storage/v1/object/sign/...
        If running offline or in mock test environment, generates a local API stream URL.
        Never generates or returns public, unauthenticated storage URLs.
        """
        # 1. Attempt Supabase signed URL generation
        if self.supabase_url and self.service_key:
            try:
                sign_url = f"{self.supabase_url}/storage/v1/object/sign/{self.bucket}/{storage_path}"
                headers = {
                    "Authorization": f"Bearer {self.service_key}",
                    "apikey": self.service_key,
                }
                payload = {"expiresIn": expires_in_seconds}
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(sign_url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        signed_relative = data.get("signedURL")
                        if signed_relative:
                            if signed_relative.startswith("http"):
                                return signed_relative
                            return f"{self.supabase_url}{signed_relative}"
            except Exception as e:
                logger.debug("Supabase signed URL generation skipped/offline: %s", e)

        # 2. Local fallback stream URL
        # Extract farm_id and report_id from storage_path if not directly provided
        parts = storage_path.split("/")
        fid = farm_id or (parts[0] if len(parts) >= 1 else "unknown")
        rid = report_id or (parts[1] if len(parts) >= 2 else "unknown")
        prefix = settings.API_V1_PREFIX
        return f"{prefix}/farms/{fid}/soil-reports/{rid}/document"

    def get_file_bytes(self, storage_path: str) -> Tuple[bytes, str]:
        """
        Retrieve document raw bytes and media type from local cache or Supabase private storage.
        """
        # 1. Check local filesystem fallback first
        local_file_path = self.local_dir / storage_path
        if local_file_path.exists() and local_file_path.is_file():
            content = local_file_path.read_bytes()
            ext = local_file_path.suffix.lower()
            mime_type = "application/pdf"
            if ext in (".jpg", ".jpeg"):
                mime_type = "image/jpeg"
            elif ext == ".png":
                mime_type = "image/png"
            return content, mime_type

        # 2. Check Supabase private storage
        if self.supabase_url and self.service_key:
            try:
                download_url = f"{self.supabase_url}/storage/v1/object/authenticated/{self.bucket}/{storage_path}"
                headers = {
                    "Authorization": f"Bearer {self.service_key}",
                    "apikey": self.service_key,
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(download_url, headers=headers)
                    if resp.status_code == 200:
                        mime_type = resp.headers.get("content-type", "application/pdf")
                        return resp.content, mime_type
            except Exception as e:
                logger.warning("Supabase storage get_file_bytes error: %s", e)

        raise FileNotFoundError(f"Soil report document not found for storage path: {storage_path}")

    def delete_file(self, storage_path: str) -> bool:
        """
        Delete document from storage (local cache and remote bucket).
        """
        deleted = False
        local_file_path = self.local_dir / storage_path
        if local_file_path.exists():
            try:
                local_file_path.unlink()
                deleted = True
            except Exception:
                pass

        if self.supabase_url and self.service_key:
            try:
                delete_url = f"{self.supabase_url}/storage/v1/object/{self.bucket}"
                headers = {
                    "Authorization": f"Bearer {self.service_key}",
                    "apikey": self.service_key,
                }
                payload = {"prefixes": [storage_path]}
                with httpx.Client(timeout=5.0) as client:
                    resp = client.request("DELETE", delete_url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        deleted = True
            except Exception:
                pass

        return deleted


# Global singleton instance
soil_report_storage = SoilReportStorageService()
