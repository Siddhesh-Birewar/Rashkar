# CropNet AI — Local Development & Prototype Startup Guide

**Document Version:** 1.0.0  
**Target Environment:** Local macOS / Linux Workstation  
**Runtime Components:** FastAPI, Ollama (`qwen3:8b`), Flutter Web (Chrome), Supabase PostgreSQL 17  

---

## Architecture Overview

In prototype mode, CropNet AI runs entirely locally:
- **FastAPI Backend:** Runs locally at `http://127.0.0.1:8000`. Acts as the single gateway for all agronomic logic, ISRIC/OpenWeather geospatial extraction, and authenticated PostgreSQL access.
- **Ollama LLM Engine:** Runs locally at `http://127.0.0.1:11434`, hosting `qwen3:8b`. The frontend never communicates directly with Ollama; all requests pass through FastAPI's strict agronomic guardrails.
- **Flutter Web Frontend:** Runs locally in Chrome at `http://localhost:8080`, communicating exclusively with FastAPI.
- **Database & Auth:** Remote Supabase project hosting PostgreSQL 17 + PostGIS and GoTrue authentication.

```
┌─────────────────────────────────┐
│     Google Chrome (Browser)     │
│   Flutter Web: localhost:8080   │
└───────────────┬─────────────────┘
                │ HTTP / REST (JWT)
                ▼
┌─────────────────────────────────┐
│    FastAPI Application Server   │
│        127.0.0.1:8000           │
│  Deterministic Agronomic Engine │
└───────┬─────────────────┬───────┘
        │                 │
        │ HTTP            │ SQL (SSL)
        ▼                 ▼
┌──────────────┐   ┌──────────────────────────────┐
│ Local Ollama │   │      Supabase Cloud          │
│ 127.0.0.1:   │   │  PostgreSQL 17.11 + PostGIS  │
│ 11434        │   │  GoTrue Auth Service         │
│ (qwen3:8b)   │   └──────────────────────────────┘
└──────────────┘
```

---

## Prerequisites

1. **Python 3.11+** with virtual environment dependencies installed.
2. **Flutter 3.29+ / Dart 3.7+** configured for web.
3. **Google Chrome** installed.
4. **Ollama** installed with `qwen3:8b` model pulled:
   ```bash
   ollama pull qwen3:8b
   ```

---

## One-Click Startup

Run the provided prototype runner script from the repository root:
```bash
./scripts/start_local_prototype.sh
```

This automated script performs:
1. Health check of Ollama on `127.0.0.1:11434` and validates `qwen3:8b` presence.
2. Starts FastAPI backend on `http://127.0.0.1:8000` (auto-reloading).
3. Launches Flutter Web on Chrome at `http://localhost:8080`.

---

## Manual Step-by-Step Startup

### 1. Ensure Local Ollama is Running
In terminal:
```bash
ollama serve
# Verify in another terminal:
curl http://127.0.0.1:11434/api/tags
```

### 2. Launch FastAPI Backend
From the `cropnet` root directory:
```bash
python3 -m uvicorn cropnet.services.api.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify backend health:
```bash
curl http://127.0.0.1:8000/api/v1/health
```
Response:
```json
{
  "status": "healthy",
  "app_name": "CropNet AI Backend",
  "environment": "development",
  "llm_runtime": {
    "provider": "ollama_local",
    "base_url": "http://127.0.0.1:11434",
    "configured_model": "qwen3:8b",
    "ollama_server_online": true,
    "model_available": true,
    "operational": true,
    "fallback_available": true
  }
}
```

Interactive OpenAPI Swagger UI is accessible at:  
`http://127.0.0.1:8000/api/v1/docs`

### 3. Launch Flutter Web Application
From `cropnet/apps/mobile`:
```bash
cd apps/mobile
flutter run -d chrome --web-port=8080 --web-hostname=localhost
```

---

## Test Accounts (Pre-Provisioned)

Due to default Supabase free tier email rate limits on open public signup, use these verified test accounts:

| Role | Email | Password | User ID (UUID) |
|---|---|---|---|
| **Primary Farmer** | `farmer1@cropnet.ai` | `[CONFIGURED_TEST_PASSWORD]` | `9c7582e5-e915-465e-a887-d32a2f48ee23` |
| **Secondary Farmer** | `farmer2@cropnet.ai` | `[CONFIGURED_TEST_PASSWORD]` | `3f4120b4-0a53-47be-9f7e-2e6fe77306f6` |

---

## Troubleshooting

- **Ollama Timeout / High Latency:** The first inference request may take 15–25 seconds while the 8B model weights load into Apple Silicon / GPU memory. Subsequent tokens stream significantly faster.
- **Deterministic Fallback Activation:** If Ollama is temporarily stopped or times out, the backend automatically invokes its deterministic fallback engine (`generation_source: "deterministic_fallback"`), ensuring 100% advisory uptime.
- **Port Conflicts:** If port 8000 is occupied, terminate existing processes via `lsof -i :8000` or specify a custom port.
