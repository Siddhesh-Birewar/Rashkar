# RASHKAR — Deployment Guide

This guide details how to deploy Rashkar in local, staging, and production environments.

---

## 1. System Architecture

Rashkar is designed as a modular, container-ready platform:
- **Frontend**: Flutter Web Single Page Application (SPA), served by any high-performance static web server (Nginx, Caddy, Cloudflare Pages).
- **Backend API**: FastAPI running on Python 3.11+ ASGI server (Uvicorn / Gunicorn).
- **Primary Database**: PostgreSQL 16 with PostGIS 3.4 for spatial geometry and agronomic registries (falls back to local SQLite for isolated testing).
- **Cache & Task Queue**: Redis 7 and Celery (optional for heavy reanalysis downloads).

---

## 2. Docker Compose Deployment

The repository includes a ready-to-run [`docker-compose.yml`](../docker-compose.yml):

```bash
# 1. Configure production environment
cp .env.example .env
# Edit .env with your production database credentials and SECRET_KEY

# 2. Build and launch services
docker compose up -d --build

# 3. Check logs
docker compose logs -f backend
```

---

## 3. Manual Production Deployment

### Backend (Systemd / Uvicorn)
1. Install Python 3.11+:
   ```bash
   python -m venv /opt/rashkar-env
   source /opt/rashkar-env/bin/activate
   pip install -r pyproject.toml
   ```
2. Run database migrations:
   ```bash
   python -c "from backend.app.db.init_db import init_db; init_db()"
   ```
3. Run with multiple workers behind a reverse proxy:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Frontend (Nginx / Flutter Web Release)
1. Build Flutter Web release:
   ```bash
   cd flutter_client
   flutter build web --release --dart-define=API_BASE_URL=https://api.yourdomain.com
   ```
2. Serve the generated `build/web/` directory with Nginx:
   ```nginx
   server {
       listen 80;
       server_name app.yourdomain.com;
       root /var/www/rashkar/build/web;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
           add_header Cache-Control "no-store, no-cache, must-revalidate";
       }
   }
   ```

---

## 4. Security Considerations
- **HTTPS**: Always run behind TLS (Let's Encrypt / Cloudflare).
- **CORS**: Configure `ALLOWED_ORIGINS` in FastAPI settings to allow only authorized frontend domains.
- **Secrets**: Never commit `.env` or production credentials. Use secrets managers (Vault, AWS Secrets Manager, GitHub Secrets).
- **Database**: Ensure PostgreSQL connections use SSL (`sslmode=require`).
