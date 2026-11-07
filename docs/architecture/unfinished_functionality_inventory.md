# CropNet AI — Unfinished Functionality & Production Roadmap Inventory

**Document Version:** 1.0.0  
**Status:** Prototype Complete / Production Postponed  
**Auditor:** Antigravity Autonomous Agent (Architecture & Release-Readiness)  

---

## 1. Executive Summary

This document provides a transparent, rigorous inventory of functionality within CropNet AI. With the official strategic decision to postpone public production deployment and focus on a local-first prototype, this inventory distinguishes:
1. **Fully Implemented & Verified Prototype Features** (Operational locally in Flutter Web + FastAPI + local Ollama `qwen3:8b`).
2. **Postponed Production Infrastructure** (Deferred until commercial cloud deployment).
3. **Future Feature Roadmap & Enhancements** (Planned capabilities beyond the prototype scope).

---

## 2. Feature Implementation Status Matrix

| Module | Feature / Capability | Prototype Status | Production Status | Technical Details / Notes |
|---|---|---|---|---|
| **Auth** | User Login with JWT | **COMPLETE** | Ready | Supabase GoTrue Auth token exchange. |
| **Auth** | Token Refresh & Session Persistence | **COMPLETE** | Ready | Persistent via `SharedPreferences`. |
| **Auth** | User Logout & Revocation | **COMPLETE** | Ready | Calls Supabase `/auth/v1/logout`. |
| **Auth** | Public User Self-Registration | **LIMITED** | Postponed | Supabase default free-tier rate limits email confirmations (HTTP 429). Requires custom SMTP provider (SendGrid/SES) in production. Test accounts used for prototype. |
| **Farms** | Interactive Polygon Boundary Drawing | **COMPLETE** | Ready | Click-to-add vertices, live geodesic area calculation, undo/clear. |
| **Farms** | PostGIS Geodesic Area & Centroid Calculation | **COMPLETE** | Ready | WGS84 ellipsoidal area in hectares & acres. |
| **Farms** | Multi-Tenant Farm Isolation (Row-Level Access) | **COMPLETE** | Ready | Cross-tenant access strictly returns HTTP 403 Forbidden. |
| **Farms** | Farm Cascade Deletion | **COMPLETE** | Ready | Cascades deletion of dependent weather snapshots and climate records before deleting farm. |
| **Soil** | ISRIC SoilGrids 2.0 Digital Extraction (250m) | **COMPLETE** | Ready | Extracts pH (H2O), CEC, clay %, sand %, SOC, and texture class. |
| **Soil** | **Agronomic Safeguard: Zero NPK Fabrication** | **COMPLETE** | Enforced | Available NPK remains strictly `null`. UI informs farmer that laboratory soil testing is required. |
| **Soil** | **Laboratory Soil Test Card Upload & OCR (Phase 5.6)** | **COMPLETE** | Ready | End-to-end multi-modal vision & text extraction (PDF/JPEG/PNG), columnar multi-sample table parsing, dual-source intelligence fusion with strict provenance separation and farmer confirmation. |
| **Weather** | Real-Time OpenWeather Conditions & Forecasts | **COMPLETE** | Ready | Fetches, caches in PostgreSQL, and serves meteorological metrics. |
| **Weather** | NASA POWER 30-Year Climatology Summary | **COMPLETE** | Ready | Mean rainfall, monsoon share %, temperature limits, drought risk. |
| **Crops** | 10 Maharashtra Pilot Crop Knowledge Profiles | **COMPLETE** | Ready | ICAR / MPKV Rahuri agronomic thresholds in PostgreSQL. |
| **Crops** | Seasonal Crop Catalogue Filters | **COMPLETE** | Ready | Kharif, Rabi, Summer, and Perennial filters. |
| **Advisory** | Deterministic Decision Engine (Phase 5.1) | **COMPLETE** | Ready | Sole authority on crop suitability; hard agronomic constraints. |
| **Advisory** | Qwen3:8B Natural Language Explanation | **COMPLETE** | Local Only | Runs locally via Ollama (`http://127.0.0.1:11434`). Hosted GPU endpoint needed for public release. |
| **Advisory** | Bilingual English & Marathi Dialogue | **COMPLETE** | Local Only | Fully supported with authentic Devanagari script generation. |
| **Advisory** | Interactive Diagnostic Follow-Up Questions | **COMPLETE** | Ready | One-tap answer submission triggers deterministic re-evaluation. |
| **Advisory** | Safe Deterministic Fallback on LLM Failure | **COMPLETE** | Ready | 100% advisory uptime even when Ollama is offline. |
| **History** | Chronological Assessment & Advisory History | **COMPLETE** | Ready | Dynamic session history tracking soil and crop evaluations. |
| **Mobile** | Native Android APK Release Build | **POSTPONED** | Future | Local development focused on Flutter Web; Android toolchain requires signed keystore for release. |
| **Mobile** | Native iOS IPA Release Build | **POSTPONED** | Future | Requires Apple Developer account and provisioning profiles. |
| **Audio** | Voice Input / Output in Marathi (ASR/TTS) | **ROADMAP** | Future | Voice assistance for non-literate farmers. |

---

## 3. Detailed Analysis of Postponed Production Work

### 3.1 Hosted Private LLM Inference
- **Current State:** Ollama is hosted locally at `http://127.0.0.1:11434` with model `qwen3:8b`.
- **Reason for Postponement:** Strategic decision to develop locally without incurring cloud GPU hosting costs (RunPod, AWS EC2, GCP Cloud Run).
- **Production Path:** Stand up a containerized vLLM or Ollama instance on a cloud VM with an NVIDIA A10G/L4/T4 GPU or private Cloud Run service, secured via private VPC peering.

### 3.2 Custom SMTP Gateway for Public Signup
- **Current State:** Pre-provisioned user test accounts (`farmer1@cropnet.ai`, `farmer2@cropnet.ai`) via Supabase Admin API.
- **Reason for Postponement:** Default Supabase free tier rate limits public registration emails.
- **Production Path:** Link an enterprise SMTP provider (e.g. AWS SES, SendGrid, or Resend) in the Supabase Authentication settings.

### 3.3 Mobile Native Store Packaging
- **Current State:** Application is verified and functional as Flutter Web running in Google Chrome, with responsive support across mobile, tablet, and desktop viewports.
- **Reason for Postponement:** Deployment to Google Play Store and Apple App Store requires code-signing certificates, developer accounts, and store review.

---

## 4. Quality & Compliance Checklist

- [x] No demo farms or fabricated fixture records (`demo-baramati-1` eliminated).
- [x] LLM never overrides or decides crop suitability.
- [x] Zero fabrication of available NPK from digital raster maps.
- [x] Strict user isolation and cross-tenant authorization checks.
- [x] Responsive layout across desktop, tablet, and mobile viewport widths.
- [x] Bilingual support in English and Marathi Devanagari.
