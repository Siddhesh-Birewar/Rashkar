# CropNet AI — Evaluation Metrics and Scoring Definitions (Phase 5.0)

**Document Version:** 1.0.0  
**Phase:** 5.0 (Intelligence Benchmark & Evaluation Framework)  
**Status:** Evaluation Standard  

---

## 1. Dual Independent Evaluation Tracks

A foundational requirement of CropNet AI benchmark evaluation is the **strict independence** of retrieval accuracy and agronomic reasoning accuracy.

> [!CRITICAL]
> **Cardinal Metric Rule:** Never combine Track A (Retrieval) and Track B (Reasoning) into a single blended score or weighted average.
> A system that retrieves the perfect passage from ICRISAT (2010) but misinterprets a 35°C reproductive heat threshold as an immediate plant mortality limit is agronomically defective. Conversely, a system that gives a sensible answer by chance from pre-training memory while retrieving an irrelevant document violates scientific traceability. Both tracks must be scored, audited, and reported independently.

```
+-------------------------------------------------------------------------------+
|                       Dual Independent Evaluation Tracks                      |
+---------------------------------------+---------------------------------------+
|   TRACK A: Retrieval Accuracy         |   TRACK B: Agronomic Reasoning        |
|   (Information Retrieval & Provenance)|   (Decision Logic & Scientific Truth) |
+---------------------------------------+---------------------------------------+
| - Source Retrieval Precision (P@K)    | - Scientific Constraint Adherence     |
| - Relevant Passage Recall (R@K)       | - Missing Parameter Detection Rate    |
| - Contextual Applicability Rate       | - Follow-up Question Precision        |
| - Granular Citation Correctness       | - Calibrated Abstention Quality       |
| - Unsupported Source Exclusion Rate   | - Hallucination Rate (Strict 0% goal) |
+---------------------------------------+---------------------------------------+
                                NO BLENDED COMPOSITE
```

---

## 2. Track A: Retrieval Accuracy Metrics

Track A measures whether the retrieval subsystem accurately accesses the verified Phase 4 knowledge base, fetches the applicable literature passages, and attaches granular citations.

### 2.1 Source Retrieval Precision and Recall ($P@K$, $R@K$)
- **Source Precision at K ($P@K$):** The proportion of retrieved sources in top-$K$ that are officially mapped in the gold-standard reference for that query.
  $$P@K = \frac{|\text{Retrieved Sources}_{1..K} \cap \text{Gold Standard Sources}|}{K}$$
- **Source Recall at K ($R@K$):** The proportion of required gold-standard sources retrieved in top-$K$.
  $$R@K = \frac{|\text{Retrieved Sources}_{1..K} \cap \text{Gold Standard Sources}|}{|\text{Gold Standard Sources}|}$$

### 2.2 Contextual Applicability Rate (CAR)
Measures whether the retrieved passage actually applies to the specific agroecological and physical context of the query (e.g. distinguishing a Vertisol recommendation from a shallow laterite soil recommendation).
$$\text{CAR} = \frac{\sum_{i=1}^N \mathbb{I}(\text{Retrieved Passage is Agroecologically Applicable}_i)}{N}$$

### 2.3 Citation Correctness Score (CCS)
Evaluates whether generated citations match valid records in `agricultural_knowledge_sources` down to the publication title and specific page/section:
- **1.0 (Exact Citation):** Source ID, publication title, and table/page match the verified record (e.g., `icar_nrcp_manage_2022`, Table 1, p. 45).
- **0.5 (Partial Citation):** Source organization or document is correct, but specific table/page is omitted or generic.
- **0.0 (Invalid/Hallucinated Citation):** Cites an unregistered source, generic web URL, or attributes data to the wrong institution (e.g. attributing pomegranate Bahar tables to ICRISAT).

### 2.4 Unsupported Source Exclusion Rate (USER)
Measures the system's ability to exclude irrelevant or unverified sources when a keyword matches superficially:
$$\text{USER} = \frac{\text{Correctly Excluded Unsupported Sources}}{\text{Total Superficial Keyword Distractors Present}}$$

---

## 3. Track B: Agronomic Reasoning Accuracy Metrics

Track B evaluates the deterministic decision engine and the LLM explanation layer on agricultural correctness, safety, and constraint adherence.

### 3.1 Scientific Constraint Adherence (SCA)
Measures whether the system strictly respects hard agronomic boundaries:
- **1.0 (Strict Adherence):** Disqualifies crops when limiting factors exceed tolerable ranges (e.g., chickpea in waterlogged soils, pomegranate in 20 cm shallow clay, sugarcane with dry well in February).
- **0.0 (Constraint Violation):** Approves a disqualified crop, treats an unverified parameter as verified, or ignores a hard physiological limit.
$$\text{Constraint Violation Rate (CVR)} = 1 - \text{SCA}$$
*(Target for CVR is strictly 0.00).*

### 3.2 Missing Parameter Detection Rate (MPDR)
Evaluates whether the system flags the absence of essential diagnostic variables (e.g., soil depth, EC, irrigation capacity) before issuing an unconditional verdict:
$$\text{MPDR} = \frac{\text{Missing Parameters Correctly Identified}}{\text{Total Missing Parameters Required in Context}}$$

### 3.3 Follow-up Question Quality (FQQ)
When critical data is missing or contradictory, evaluates the generated clarification questions:
- **1.0 (High Quality):** Questions are targeted, non-leading, clinically precise, and provide sensible categorical options (e.g., "What is your effective soil depth: Shallow <30 cm, Medium 30–60 cm, or Deep >60 cm?").
- **0.5 (Moderate Quality):** Vague question asked (e.g., "Please tell me more about your soil").
- **0.0 (Poor/Absent):** Fails to ask necessary clarification questions and makes ungrounded assumptions.

### 3.4 Calibrated Abstention Quality (CAQ)
Evaluates the system's ability to refuse or qualify answers when evidence is missing or out of scope (e.g., Dragon Fruit query, zero-context queries):
- **1.0 (Perfect Abstention):** Explicitly states data insufficiency, defines the boundary of verified knowledge, and refuses to guess.
- **0.0 (Uncalibrated Overconfidence):** Hallucinates a prescription for an unverified crop or fabricates a scientific threshold.

### 3.5 Hallucination Rate (HR)
The frequency of generated numbers, thresholds, or causal mechanisms that have zero presence in the retrieved database context:
$$\text{HR} = \frac{\text{Test Cases with Hallucinated Numerical Thresholds}}{\text{Total Evaluated Cases}}$$
*(CropNet target is strictly 0.00. Unverified limits such as pomegranate lower pH or annual water mm must remain NULL or be stated as unverified).*

---

## 4. Specialized Performance Dimensions

### 4.1 Multilingual Marathi Quality (MMQ)
Evaluates the fluency, vernacular accuracy, and semantic parity of Marathi responses against English benchmarks:
- **Terminological Fidelity:** Uses approved Marathi agricultural terms:
  - Soil pH $\rightarrow$ **जमिनीचा सामू**
  - Soil Organic Carbon $\rightarrow$ **सेंद्रिय कर्ब**
  - Available Nitrogen $\rightarrow$ **उपलब्ध नत्र**
  - Vertisols / Black soil $\rightarrow$ **काळी माती / भारी जमीन**
  - Drainage $\rightarrow$ **पाण्याचा निचरा**
  - Waterlogging $\rightarrow$ **पाणथळ स्थिती / पाणी साचणे**
  - Bahar regulation $\rightarrow$ **बहार व्यवस्थापन (मृग, हस्त, आंबिया)**
  - Reproductive stage $\rightarrow$ **पुनरुत्पादन अवस्था**
  - Flower drop $\rightarrow$ **फूल गळ**
  - Pod set $\rightarrow$ **घाटे धारणा**
- **Cross-Lingual Numerical Parity:** Asserts that every numerical value in English appears identically in Marathi (e.g. ३५°C $\leftrightarrow$ 35°C, ६.५–७.० $\leftrightarrow$ 6.5–7.0).

### 4.2 System Latency & Resource Consumption
- **Response Latency:**
  - $p50 \le 1.50\text{ seconds}$
  - $p95 \le 3.50\text{ seconds}$
  - $p99 \le 5.00\text{ seconds}$
- **Throughput:** Minimum 15 tokens/sec generation on local target hardware.
- **VRAM Footprint:** Maximum 6.5 GB VRAM utilization for local 8B model (4-bit / 8-bit quantized baseline).

---

## 5. Scoring Protocols & Anti-Fabrication Safeguards

### No Probabilities as Calibrated Scores
Under no circumstances shall raw softmax probabilities, uncalibrated logit confidences, or heuristic percentages be reported to farmers as "confidence scores" (e.g. claiming "92.4% confident this crop is suitable"). 

The system reports discrete, evidence-grounded states:
- `VERIFIED_SUITABLE`
- `REGIONAL_SCREENING_ONLY`
- `REQUIRES_REGIONAL_VALIDATION`
- `CONDITIONALLY_SUITABLE_PENDING_DATA`
- `UNSUITABLE_VIOLATION`
- `ABSTAIN_INSUFFICIENT_EVIDENCE`
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/evaluation_metrics_and_scoring.md
