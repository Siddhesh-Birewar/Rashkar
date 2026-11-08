import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

def compute_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

def download_file(url: str, dest_path: Path, timeout: float = 60.0, headers: Optional[Dict[str, str]] = None) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True, headers=headers) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    return dest_path
