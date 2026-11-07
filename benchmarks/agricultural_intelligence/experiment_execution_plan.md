# CropNet AI — Agricultural Intelligence Experiment Execution Plan (Phase 5.0)

**Document Version:** 1.0.0  
**Phase:** 5.0 (Intelligence Benchmark & Evaluation Framework)  
**Target Architecture:** Model-Independent Evaluation Harness (`CropNetAgriEvalRunner`)  
**Baseline Model:** Local Qwen3:8B (Instruction-Tuned, 4-bit / 8-bit quantized) + Local Dense Embeddings Baseline  
**Execution Scope:** Rigorous Offline Benchmark Evaluation (Zero Online Downloads or Fine-Tuning in Phase 5.0)  

---

## 1. Model-Independent Evaluation Harness Design

To ensure evaluation integrity, CropNet implements a modular, model-independent evaluation runner interface (`CropNetAgriEvalRunner`). The runner isolates model inference from scoring and logging, allowing any LLM or rule engine to be evaluated against the 30-case gold-standard benchmark.

```
+-------------------------------------------------------------------------------+
|                       CropNetAgriEvalRunner Pipeline                          |
+-------------------------------------------------------------------------------+
| 1. Benchmark Loader (Loads benchmark_dataset.json & gold_standard_mapping.md) |
| 2. Context Builder (Simulates farm profile, retrieves DB records & citations) |
| 3. Candidate Model Execution (Dispatches structured prompt to Local Qwen3:8B) |
| 4. Deterministic Parser (Extracts decisions, numbers, citations, questions)   |
| 5. Track A Evaluator (Computes Retrieval P@K, Recall, Applicability, USER)    |
| 6. Track B Evaluator (Computes Constraint Adherence, MPDR, FQQ, CAQ, Halluc)  |
| 7. Linguistic Evaluator (Terminological check, BLEU/chrF against Marathi GT)  |
| 8. Telemetry Recorder (Logs Latency, VRAM, Tokens/sec, Exit Codes)           |
| 9. Artifact Generator (Generates comprehensive evaluation_report.json & .md)  |
+-------------------------------------------------------------------------------+
```

---

## 2. Baseline Model & Embedding Environment

In strict accordance with Phase 5.0 restrictions:
- **No new AI models will be downloaded.**
- **No models will be fine-tuned.**
- **Baseline LLM:** The existing local **Qwen3:8B** instance running via local inference server (e.g. Ollama or llama.cpp backend at `http://localhost:11434` or local Python bindings).
- **Baseline Dense Retriever:** Existing local embedding baseline (`BAAI/bge-small-en-v1.5` or `sentence-transformers/all-MiniLM-L6-v2`) for passage matching, augmented with deterministic SQL filtering on `crop_id`, `taluka`, and `soil_texture`.

---

## 3. Evaluation Protocol & Execution Steps

### Step 1: Input Pre-Flight & Normalization
The evaluation harness loads `benchmark_dataset.json`. Each test case is parsed into:
- System Context (Taluka, soil parameters, weather forecast, crop catalog).
- User Query (English or Marathi).
- Gold-Standard Truth (Allowed boundaries, prohibited claims, citations, follow-up criteria).

### Step 2: Prompt Construction (Structured JSON In / Out)
To prevent ungrounded hallucinations, the prompt template strictly passes deterministic data payloads:

```text
SYSTEM PROMPT:
You are CropNet AI, a precision agricultural intelligence assistant for Maharashtra, India.
You must generate recommendations based EXCLUSIVELY on the provided agricultural context payload.
RULES:
1. Never invent or adjust numerical thresholds (pH, temperatures, water volumes).
2. If a parameter is marked NULL or unverified in the context, explicitly state that it is unverified.
3. Decouple agronomic suitability from financial profitability.
4. When essential limiting factors are missing or contradictory, state the uncertainty and ask targeted follow-up questions.
5. In Marathi responses, use precise agricultural terminology (सामू, सेंद्रिय कर्ब, पाणथळ, बहार).

CONTEXT PAYLOAD:
{context_payload_json}

USER QUERY:
{user_query}
```

### Step 3: Dual Independent Scoring Execution
The response is parsed and passed to the dual evaluation tracks:

#### Track A Evaluation (Retrieval Accuracy):
1. **Source Attribution Check:** Verify that every citation in the response exists in `gold_standard_source_mapping.md`.
2. **Unsupported Source Exclusion:** Verify that distractor sources (e.g. canal Vertisol recommendations applied to Maval gravel) are omitted.
3. **Citation Precision:** Check document title and page/table specificity.

#### Track B Evaluation (Agronomic Reasoning Accuracy):
1. **Constraint Checker:** Verify that disqualified crops are never marked suitable.
2. **Numeric Extractor:** Extract all numbers and regex patterns (`\d+(\.\d+)?\s*(°C|mm|pH|L|kg/ha)`) and verify set membership in the gold-standard payload. Any external number triggers a **Hallucination Flag**.
3. **Missing Parameter Checker:** If the test case is `AGRI-BENCH-004` (missing EC) or `AGRI-BENCH-014` (missing profile), verify that the response refuses unconditional ranking.
4. **Follow-Up Quality Evaluator:** Verify that clarification questions match the required missing parameters.

#### Specialized Linguistic Evaluation:
1. **Marathi Agricultural Lexicon Matcher:** Check for mandatory presence of key terms (`सामू`, `सेंद्रिय कर्ब`, `निचरा`, `बहार`, `पुनरुत्पादन अवस्था`).
2. **Cross-Lingual Invariant Check (`AGRI-BENCH-029`):** Verify numerical identity across English and Marathi runs.

---

## 4. Experiment Metrics Scorecard & Target Thresholds

| Metric ID | Metric Name | Evaluation Track | Target Threshold | Critical Failure Boundary |
|:---:|---|:---:|:---:|:---:|
| **M-01** | Source Retrieval Precision ($P@1$) | Track A | $\ge 0.95$ | $< 0.80$ |
| **M-02** | Granular Citation Correctness (CCS) | Track A | $\ge 0.90$ | $< 0.70$ |
| **M-03** | Unsupported Source Exclusion (USER) | Track A | $1.00$ (100%) | $< 0.90$ |
| **M-04** | Scientific Constraint Adherence (SCA) | Track B | $1.00$ (100%) | $< 0.95$ (Any crop violation is critical) |
| **M-05** | Numerical Hallucination Rate (HR) | Track B | $0.00$ (0%) | $> 0.00$ (Zero tolerance policy) |
| **M-06** | Missing Parameter Detection Rate (MPDR)| Track B | $\ge 0.90$ | $< 0.75$ |
| **M-07** | Follow-Up Question Precision (FQQ) | Track B | $\ge 0.85$ | $< 0.65$ |
| **M-08** | Calibrated Abstention Quality (CAQ) | Track B | $1.00$ (100%) | $< 0.90$ |
| **M-09** | Marathi Terminological Fidelity (MTF) | Language | $\ge 0.90$ | $< 0.75$ |
| **M-10** | Cross-Lingual Numerical Parity (CLNP) | Language | $1.00$ (100%) | $< 1.00$ |
| **M-11** | End-to-End Latency ($p95$) | Systems | $\le 4.0\text{ s}$ (Provisional) | $> 6.0\text{ s}$ |
| **M-12** | Peak Process Memory (RSS) | Systems | $\le 6.5\text{ GB}$ (Provisional) | $> 8.0\text{ GB}$ |
| **M-13** | Time to First Token ($p95$ TTFT) | Systems | $\le 1.5\text{ s}$ (Provisional) | $> 2.5\text{ s}$ |
| **M-14** | Generation Throughput (TPS) | Systems | $\ge 15.0\text{ tokens/s}$ (Provisional) | $< 8.0\text{ tokens/s}$ |
| **M-15** | System Memory Pressure Level | Systems | `NORMAL` (Level 1) | `WARNING` or `CRITICAL` |

*(Note: Hardware metrics are tailored for Apple Silicon unified memory architecture measuring Resident Set Size and Darwin kernel memory pressure. Numerical targets are provisional baselines to be calibrated during Phase 5.3 benchmarks; zero model inference is executed in Phase 5.0).*

---

## 5. Experiment Artifact Deliverables

Upon running the experiment suite in Phase 5.1/5.3, the runner generates three persistent artifacts:
1. `benchmarks/runs/run_<timestamp>_results.json`: Full execution logs with raw inputs, outputs, tokens, latencies, and parsed values for all 30 test cases.
2. `benchmarks/runs/run_<timestamp>_summary.md`: Human-readable summary scorecard detailing Track A and Track B performances, failed adversarial cases, and latency charts.
3. `benchmarks/runs/run_<timestamp>_diff_audit.txt`: Line-by-line comparison of any numerical deviations between model outputs and gold-standard boundaries.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/experiment_execution_plan.md
