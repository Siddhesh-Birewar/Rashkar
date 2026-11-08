# RASHKAR — Local Ollama AI Integration Architecture
**Edge LLM Grounding & Deterministic Fallback Strategy**  
**Document ID:** RASHKAR-DOC-AI-01  
**Runtime:** Developer Environment (Local PC)  
**Version:** 2.0

---

## 1. Overview and Core Philosophy

Rashkar supports an optional edge AI assistant powered by **Ollama** running locally on the development machine (`http://127.0.0.1:11434`). 

The foundational principle of Rashkar's AI design is:  
**The Large Language Model is an interface and explanation engine, NOT a calculation engine.**

All biophysical calculations (Liljegren WBGT, crop critical thermal hours, soil water retention, NABARD financial cash flows) are executed strictly in deterministic Python services. The pre-calculated numbers are then passed as grounded context into the model's prompt. Under no circumstances is the LLM permitted to fabricate temperatures, yields, costs, or medical recommendations.

---

## 2. Local Environment & Model Verification

- **Endpoint:** `http://127.0.0.1:11434/api/tags`
- **Installed Model:** `qwen3:8b` (Alibaba Cloud Qwen 2.5 / 3 generation, 8.2 billion parameters, Q4_K_M quantized GGUF).
- **Latency / Performance:** ~15–25 tokens/second on modern local GPUs/CPUs.
- **Privacy & Connectivity:** Fully offline; zero external telemetry or cloud API dependencies.

---

## 3. Prompt Grounding & System Directives

When a farmer asks a question via `Ask Rashkar`, the backend constructs a grounded prompt incorporating:
1. **Farmer & Farm Profile:** District, taluka, crop, stage, days after sowing, irrigation type.
2. **Current Micro-Weather:** Live temperature, humidity, wind, rainfall, solar radiation.
3. **Engine Risk Assessments:** Pre-calculated Worker WBGT hazard level and Crop Heat Risk level.
4. **Strict Safety Rules:**
   - Never recommend pesticide dosages beyond official CIBRC / University recommendations.
   - For heat illness, prioritize cooling and medical care.
   - Never predict harvest dates or monetary profits out of thin air.

### Example Grounded System Prompt Template
```text
You are Rashkar Assistant, an expert agronomist and farm safety advisor for Maharashtra, India.
Always answer concisely in simple, clear language. Do not invent numbers.

CURRENT FARM CONTEXT:
- Location: {district}, {taluka}
- Crop: {crop_name} (Stage: {stage_name}, {das} days after sowing)
- Current Weather: {temp}°C, {humidity}% RH, Wind {wind} km/h
- Worker Heat Risk: {worker_hazard_level} (WBGT: {wbgt}°C)
- Crop Heat Risk: {crop_heat_level} (Critical Threshold: {crit_temp}°C)

Use ONLY the provided context. If information is missing, advise the farmer to consult their local Krishi Vigyan Kendra (KVK).
```

---

## 4. Deterministic Fallback Mechanism

If the Ollama daemon is stopped, unreachable, or takes longer than 4.0 seconds to respond, Rashkar automatically activates the deterministic template fallback:
- Pre-compiled agronomic rule templates for each crop, stage, and hazard condition.
- Zero latency (< 5ms response).
- 100% uptime guarantee for the mobile and web client.

This hybrid approach ensures high resilience: edge AI intelligence when available, unbreakable deterministic safety when offline.

---

## 5. Verification & Pytest Coverage

Verified by automated pytest test suite in `backend/tests/test_assistant.py`:
- `test_assistant_chat_grounded_response`: Verifies grounded context injection and response structure.
- `test_assistant_chat_crop_question`: Verifies agronomic question routing with farm profile parameters.
Both tests pass reliably.
