"""
Comprehensive Security and Access Control Remediation Test Suite (Requirement R1).

Verifies:
1. Hardcoded production credentials eradicated from configuration and source.
2. Configuration requires secure environment variables; rotation readiness.
3. Fail-closed authentication: missing auth returns 401 (never silently impersonates DEV_USER_ID).
4. Opt-in development bypass (X-Dev-User-Id) is strictly gated via ALLOW_DEV_AUTH_BYPASS=True.
5. Dev bypass is strictly rejected in production environments.
6. Decision and farm ownership enforcement across:
   - POST /api/v1/agriculture/evaluate-farm
   - GET /api/v1/agriculture/decision/{decision_id}
   - GET /api/v1/farms/decision/{decision_id}
   - POST /api/v1/agriculture/explain-decision
   - POST /api/v1/agriculture/follow-up
   - POST /api/v1/agriculture/conversation
"""
import os
import uuid
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from cropnet.services.api.app.core.config import Settings, settings
from cropnet.services.api.app.main import app

client = TestClient(app)

USER_A_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_B_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

AUTH_USER_A = {"X-Dev-User-Id": str(USER_A_ID)}
AUTH_USER_B = {"X-Dev-User-Id": str(USER_B_ID)}


class TestConfigSecurity:
    """Verifies that configuration does not contain hardcoded secrets and requires env vars."""

    def test_no_hardcoded_supabase_passwords_in_source_or_defaults(self):
        """Hardcoded production database password must not exist in config.py or default settings."""
        config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../app/core/config.py")
        )
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "rAO6B8K2yQzFXlw8" not in content, "Leaked Supabase password found in config.py!"
        assert "glnpmpagajfurpmlinvd" not in content, "Live project ref found in config.py defaults!"

        # Fresh Settings instance without env file override
        s = Settings()
        assert s.DATABASE_URL is None
        assert s.SYNC_DATABASE_URL is None

    def test_opt_in_dev_auth_bypass_default_is_false(self):
        """ALLOW_DEV_AUTH_BYPASS must default to False (fail-closed)."""
        s = Settings()
        assert s.ALLOW_DEV_AUTH_BYPASS is False

    def test_production_rejects_dev_auth_bypass_at_startup(self):
        """Settings validation must raise error if ALLOW_DEV_AUTH_BYPASS=True in production."""
        with pytest.raises((ValidationError, ValueError)):
            Settings(
                ENVIRONMENT="production",
                ALLOW_DEV_AUTH_BYPASS=True,
                CORS_ORIGINS=["https://app.cropnet.ai"],
                SYNC_DATABASE_URL="postgresql://user:pass@host:5432/db"
            )

    def test_database_urls_require_environment_variables_not_defaults(self):
        """Database URLs must default to None and require explicit environment variable injection."""
        s = Settings()
        assert s.DATABASE_URL is None
        assert s.SYNC_DATABASE_URL is None
        # When environment variables are provided, they are correctly accepted
        s_custom = Settings(
            DATABASE_URL="postgresql+asyncpg://app_user:safe_pass@db.internal:5432/cropnet",
            SYNC_DATABASE_URL="postgresql://app_user:safe_pass@db.internal:5432/cropnet"
        )
        assert s_custom.DATABASE_URL == "postgresql+asyncpg://app_user:safe_pass@db.internal:5432/cropnet"
        assert s_custom.SYNC_DATABASE_URL == "postgresql://app_user:safe_pass@db.internal:5432/cropnet"


class TestFailClosedAuthentication:
    """Verifies fail-closed authentication and development bypass isolation."""

    def test_unauthenticated_request_fails_closed_with_401(self, monkeypatch):
        """
        Unauthenticated requests must never silently impersonate DEV_USER_ID.
        Must return HTTP 401 Unauthorized with WWW-Authenticate header.
        """
        monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_BYPASS", True)
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")

        resp = client.get("/api/v1/farms")
        assert resp.status_code == 401
        assert "Bearer" in resp.headers.get("www-authenticate", "")

    def test_dev_bypass_disabled_rejects_x_dev_user_id_with_401(self, monkeypatch):
        """When ALLOW_DEV_AUTH_BYPASS=False, X-Dev-User-Id is rejected with 401."""
        monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_BYPASS", False)
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")

        resp = client.get("/api/v1/farms", headers=AUTH_USER_A)
        assert resp.status_code == 401

    def test_dev_bypass_enabled_accepts_valid_uuid(self, monkeypatch):
        """When ALLOW_DEV_AUTH_BYPASS=True in dev, valid X-Dev-User-Id authenticates caller."""
        monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_BYPASS", True)
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")

        resp = client.get("/api/v1/farms", headers=AUTH_USER_A)
        assert resp.status_code == 200

    def test_dev_bypass_enabled_rejects_malformed_uuid(self, monkeypatch):
        """Malformed UUID in X-Dev-User-Id returns 400 Bad Request."""
        monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_BYPASS", True)
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")

        resp = client.get("/api/v1/farms", headers={"X-Dev-User-Id": "invalid-not-a-uuid"})
        assert resp.status_code == 400

    def test_production_mode_rejects_dev_bypass_unconditionally(self, monkeypatch):
        """In production, X-Dev-User-Id is always rejected with 401."""
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_BYPASS", True)

        resp = client.get("/api/v1/farms", headers=AUTH_USER_A)
        assert resp.status_code == 401
        assert "Bearer" in resp.headers.get("www-authenticate", "")


class TestDecisionOwnershipEnforcement:
    """Verifies that decision endpoints enforce caller and farm ownership."""

    def test_endpoints_reject_unauthenticated_requests_with_401(self):
        """All decision routes must return 401 when accessed without authentication."""
        assert client.post("/api/v1/agriculture/evaluate-farm", json={}).status_code == 401
        assert client.get("/api/v1/agriculture/decision/dec_test").status_code == 401
        assert client.get("/api/v1/farms/decision/dec_test").status_code == 401
        assert client.post("/api/v1/agriculture/explain-decision", json={"decision_id": "dec_test"}).status_code == 401
        assert client.post("/api/v1/agriculture/follow-up", json={"decision_id": "dec_test", "answers": {}}).status_code == 401
        assert client.post("/api/v1/agriculture/conversation", json={"decision_id": "dec_test", "message": "Hi"}).status_code == 401

    def test_nonexistent_decision_returns_404_for_authenticated_caller(self):
        """Requesting a non-existent decision returns 404 Not Found."""
        resp = client.get("/api/v1/agriculture/decision/dec_nonexistent_123", headers=AUTH_USER_A)
        assert resp.status_code == 404

        resp_alias = client.get("/api/v1/farms/decision/dec_nonexistent_123", headers=AUTH_USER_A)
        assert resp_alias.status_code == 404

    def test_owner_can_evaluate_and_retrieve_decision(self):
        """The user who evaluated a decision can retrieve and explain it."""
        eval_payload = {
            "taluka": "Baramati",
            "soil_ph": 7.5,
            "soil_texture": "Clay loam",
            "target_crops": ["chickpea"],
            "target_season": "rabi"
        }
        # 1. User A evaluates farm
        r_eval = client.post("/api/v1/agriculture/evaluate-farm", json=eval_payload, headers=AUTH_USER_A)
        assert r_eval.status_code == 200
        dec_id = r_eval.json()["decision_id"]

        # 2. User A retrieves decision via /agriculture/decision/{id}
        r_get = client.get(f"/api/v1/agriculture/decision/{dec_id}", headers=AUTH_USER_A)
        assert r_get.status_code == 200
        assert r_get.json()["decision_id"] == dec_id

        # 3. User A retrieves decision via /farms/decision/{id}
        r_alias = client.get(f"/api/v1/farms/decision/{dec_id}", headers=AUTH_USER_A)
        assert r_alias.status_code == 200
        assert r_alias.json()["decision_id"] == dec_id

        # 4. User A requests explanation
        from unittest.mock import patch
        mock_resp = {"message": {"content": "Chickpea is suitable for Baramati rabi season."}}
        with patch("cropnet.services.api.app.services.llm.ollama_client.OllamaClient.chat_completion", return_value=mock_resp):
            r_exp = client.post(
                "/api/v1/agriculture/explain-decision",
                json={"decision_id": dec_id, "language": "en"},
                headers=AUTH_USER_A
            )
            assert r_exp.status_code == 200
            assert r_exp.json()["decision_id"] == dec_id

    def test_unauthorized_user_cannot_access_or_explain_others_decision(self):
        """User B must be forbidden (403) from accessing or explaining User A's decision."""
        eval_payload = {
            "taluka": "Baramati",
            "soil_ph": 7.5,
            "soil_texture": "Clay loam",
            "target_crops": ["chickpea"],
            "target_season": "rabi"
        }
        # 1. User A generates decision
        r_eval = client.post("/api/v1/agriculture/evaluate-farm", json=eval_payload, headers=AUTH_USER_A)
        assert r_eval.status_code == 200
        dec_id = r_eval.json()["decision_id"]

        # 2. User B tries to retrieve User A's decision -> 403 Forbidden
        r_get_b = client.get(f"/api/v1/agriculture/decision/{dec_id}", headers=AUTH_USER_B)
        assert r_get_b.status_code == 403
        assert "permission" in r_get_b.json()["detail"].lower()

        # 3. User B tries to retrieve via /farms/decision alias -> 403 Forbidden
        r_alias_b = client.get(f"/api/v1/farms/decision/{dec_id}", headers=AUTH_USER_B)
        assert r_alias_b.status_code == 403

        # 4. User B tries to explain User A's decision -> 403 Forbidden
        r_exp_b = client.post(
            "/api/v1/agriculture/explain-decision",
            json={"decision_id": dec_id, "language": "en"},
            headers=AUTH_USER_B
        )
        assert r_exp_b.status_code == 403

        # 5. User B tries follow-up on User A's decision -> 403 Forbidden
        r_fu_b = client.post(
            "/api/v1/agriculture/follow-up",
            json={"decision_id": dec_id, "answers": {"drainage": "Well-drained"}},
            headers=AUTH_USER_B
        )
        assert r_fu_b.status_code == 403

        # 6. User B tries conversation on User A's decision -> 403 Forbidden
        r_conv_b = client.post(
            "/api/v1/agriculture/conversation",
            json={"decision_id": dec_id, "message": "Can I grow cotton?"},
            headers=AUTH_USER_B
        )
        assert r_conv_b.status_code == 403

    def test_evaluate_farm_validates_farm_ownership(self):
        """Evaluating with a farm_id requires the caller to own that registered farm."""
        # Create a farm registered to User A
        farm_payload = {
            "name": "Security Test Farm A",
            "village": "Malegaon",
            "taluka": "Baramati",
            "district": "Pune",
            "state": "Maharashtra",
            "survey_number": "77/A",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[74.57, 18.15], [74.58, 18.15], [74.58, 18.16], [74.57, 18.16], [74.57, 18.15]]]
            }
        }
        r_create = client.post("/api/v1/farms", json=farm_payload, headers=AUTH_USER_A)
        assert r_create.status_code == 201
        farm_a_id = r_create.json()["id"]

        # User B attempts to evaluate User A's farm -> 403 Forbidden
        eval_payload = {
            "farm_id": farm_a_id,
            "target_crops": ["wheat"]
        }
        r_eval_b = client.post("/api/v1/agriculture/evaluate-farm", json=eval_payload, headers=AUTH_USER_B)
        assert r_eval_b.status_code == 403
        assert "permission" in r_eval_b.json()["detail"].lower()

        # Nonexistent farm -> 404 Not Found
        random_farm_id = str(uuid.uuid4())
        r_eval_404 = client.post(
            "/api/v1/agriculture/evaluate-farm",
            json={"farm_id": random_farm_id, "target_crops": ["wheat"]},
            headers=AUTH_USER_A
        )
        assert r_eval_404.status_code == 404

        # Owner (User A) can evaluate their own farm
        r_eval_a = client.post("/api/v1/agriculture/evaluate-farm", json=eval_payload, headers=AUTH_USER_A)
        assert r_eval_a.status_code == 200
        dec_id = r_eval_a.json()["decision_id"]

        # And User A can retrieve the decision
        r_dec = client.get(f"/api/v1/agriculture/decision/{dec_id}", headers=AUTH_USER_A)
        assert r_dec.status_code == 200
