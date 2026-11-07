"""
Tests for CORS security configuration and production authentication enforcement.
"""
import os
import sys
import types
import pytest
from pydantic import ValidationError

from cropnet.services.api.app.core.config import Settings
from cropnet.services.api.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestCORSOriginsConfig:
    """Test CORS_ORIGINS parsing and production validation."""

    def test_default_cors_origins_are_explicit_localhost(self):
        """Default CORS_ORIGINS must NOT contain wildcard."""
        settings = Settings()
        assert "*" not in settings.CORS_ORIGINS
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8000" in settings.CORS_ORIGINS

    def test_parse_cors_origins_from_comma_string(self):
        """Parse comma-delimited CORS_ORIGINS env var."""
        settings = Settings(CORS_ORIGINS="https://app.cropnet.ai,https://cropnet.ai")
        assert "https://app.cropnet.ai" in settings.CORS_ORIGINS
        assert "https://cropnet.ai" in settings.CORS_ORIGINS
        assert len(settings.CORS_ORIGINS) == 2

    def test_parse_cors_origins_from_json_array_string(self):
        """Parse JSON array CORS_ORIGINS env var."""
        settings = Settings(CORS_ORIGINS='["https://app.cropnet.ai", "https://cropnet.ai"]')
        assert "https://app.cropnet.ai" in settings.CORS_ORIGINS
        assert "https://cropnet.ai" in settings.CORS_ORIGINS

    def test_production_wildcard_cors_raises_validation_error(self):
        """Production wildcard CORS must raise ValidationError at startup."""
        with pytest.raises((ValidationError, ValueError)):
            Settings(ENVIRONMENT="production", CORS_ORIGINS=["*"])

    def test_production_explicit_cors_is_valid(self):
        """Production with explicit origins must pass validation."""
        settings = Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS="https://app.cropnet.ai,https://cropnet.ai"
        )
        assert "https://app.cropnet.ai" in settings.CORS_ORIGINS
        assert "https://cropnet.ai" in settings.CORS_ORIGINS

    def test_production_empty_cors_raises_validation_error(self):
        """Production with empty CORS_ORIGINS must raise ValidationError."""
        with pytest.raises((ValidationError, ValueError)):
            Settings(ENVIRONMENT="production", CORS_ORIGINS=[])


class TestCORSMiddlewareBehavior:
    """Test actual CORS response headers."""

    def test_allowed_origin_receives_cors_header(self):
        """An allowed origin must receive Access-Control-Allow-Origin."""
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_disallowed_origin_does_not_receive_cors_header(self):
        """A disallowed origin must NOT receive Access-Control-Allow-Origin."""
        response = client.get(
            "/",
            headers={"Origin": "http://evil.com"}
        )
        origin_header = response.headers.get("access-control-allow-origin", "")
        assert origin_header != "http://evil.com"
        assert origin_header != "*"

    def test_cors_preflight_allowed_origin(self):
        """Preflight OPTIONS request from allowed origin returns 200 with credentials."""
        response = client.options(
            "/api/v1/farms",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_preflight_disallowed_origin(self):
        """Preflight OPTIONS request from disallowed origin returns 400."""
        response = client.options(
            "/api/v1/farms",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            }
        )
        # Starlette returns 400 for disallowed preflight origins
        assert response.status_code == 400


class TestProductionAuthEnforcement:
    """Test that production mode enforces Bearer token authentication."""

    def test_production_mode_blocks_dev_user_id_and_returns_401(self, monkeypatch):
        """In production, X-Dev-User-Id is strictly blocked and 401 is returned."""
        from cropnet.services.api.app.core import config
        monkeypatch.setattr(config.settings, "ENVIRONMENT", "production")

        response = client.get(
            "/api/v1/farms",
            headers={"X-Dev-User-Id": "00000000-0000-0000-0000-000000000001"}
        )
        assert response.status_code == 401
        assert "Bearer" in response.headers.get("www-authenticate", "")

    def test_production_mode_missing_auth_returns_401(self, monkeypatch):
        """In production, missing auth returns 401 with WWW-Authenticate header."""
        from cropnet.services.api.app.core import config
        monkeypatch.setattr(config.settings, "ENVIRONMENT", "production")

        response = client.get("/api/v1/farms")
        assert response.status_code == 401
        assert "Bearer" in response.headers.get("www-authenticate", "")
