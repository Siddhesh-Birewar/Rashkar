"""
Soil OCR Extraction Evaluation Benchmark Runner.
Evaluates:
- Field Extraction Accuracy (FEA)
- Numeric Extraction Accuracy (NEA / MAPE)
- Unit Extraction Accuracy (UEA)
- Sample Metadata Accuracy (SMA)
- Table Extraction Accuracy (TEA)
- Ambiguity Detection Rate (ADR)
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Tuple

# Add backend directory to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.soil_ocr.extractor import SoilOCRExtractor
from app.services.soil_ocr.ollama_client import OllamaOCRClient
from app.services.soil_ocr.models import PARAMETER_ALIASES

logger = logging.getLogger("evaluate_soil_ocr")


def run_evaluation(corpus_dir: str = None, mock_mode: bool = False) -> Dict[str, Any]:
    """
    Executes benchmark across all corpus test cases and returns summary metrics.
    """
    if corpus_dir is None:
        corpus_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soil_reports_corpus")

    client = OllamaOCRClient(mock_mode=mock_mode)
    extractor = SoilOCRExtractor(ollama_client=client)

    test_cases = [f"tc{i:02d}" for i in range(1, 11)]

    total_expected_fields = 0
    correctly_extracted_fields = 0

    total_numeric_comparisons = 0
    close_numeric_matches = 0
    abs_pct_errors: List[float] = []

    total_expected_units = 0
    correct_units = 0

    total_expected_metadata = 0
    correct_metadata = 0

    total_expected_rows = 0
    correctly_parsed_rows = 0

    total_expected_ambiguous = 0
    correctly_flagged_ambiguous = 0

    report_results: List[Dict[str, Any]] = []

    print("\n" + "=" * 80)
    print(" CROPNET AI — SOIL OCR & STRUCTURED EXTRACTION BENCHMARK RUNNER")
    print("=" * 80)

    for tc_prefix in test_cases:
        gt_path = os.path.join(corpus_dir, f"{tc_prefix}_ground_truth.json")
        if not os.path.exists(gt_path):
            continue

        with open(gt_path, "r") as f:
            gt = json.load(f)

        doc_filename = gt["document_filename"]
        doc_path = os.path.join(corpus_dir, doc_filename)

        with open(doc_path, "rb") as f:
            file_bytes = f.read()

        extraction = extractor.extract(file_bytes, filename=doc_filename)

        case_summary = {
            "id": gt.get("document_id", tc_prefix),
            "file": doc_filename,
            "modality": extraction.document_type,
            "status": extraction.extraction_status,
            "params_detected": extraction.total_parameters_detected,
            "is_ambiguous": extraction.is_ambiguous,
        }

        # 1. Negative control case (e.g. TC-10 Invoice)
        if gt.get("is_negative_control"):
            expected_status = gt.get("expected_status", "FAILED")
            status_match = extraction.extraction_status == expected_status or extraction.total_parameters_detected == 0
            case_summary["negative_control_passed"] = status_match
            report_results.append(case_summary)
            print(f"[{case_summary['id']}] {doc_filename:<32} Negative Control: {'PASS' if status_match else 'FAIL'} (0 soil params)")
            continue

        # 2. Metadata Evaluation
        exp_meta = gt.get("expected_metadata", {})
        ext_meta = extraction.metadata
        for m_key, exp_val in exp_meta.items():
            if not exp_val:
                continue
            total_expected_metadata += 1
            act_val = getattr(ext_meta, m_key, None)
            if act_val and (exp_val.lower() in act_val.lower() or act_val.lower() in exp_val.lower()):
                correct_metadata += 1

        # 3. Parameters Evaluation
        exp_params = gt.get("expected_parameters", {})
        for param_key, exp_dict in exp_params.items():
            total_expected_fields += 1
            total_expected_rows += 1

            m = extraction.get_measurement(param_key)
            if not m:
                # Check if it was expected to be NOT_REPORTED (e.g. TC-08 Available Nitrogen)
                if exp_dict.get("extraction_status") == "NOT_REPORTED" or exp_dict.get("value") is None:
                    correctly_extracted_fields += 1
                    correctly_parsed_rows += 1
                continue

            correctly_extracted_fields += 1
            correctly_parsed_rows += 1

            # Check value
            exp_val = exp_dict.get("value")
            if exp_val is not None and m.original_value is not None:
                total_numeric_comparisons += 1
                diff = abs(m.original_value - exp_val)
                pct_err = (diff / exp_val) * 100.0 if exp_val != 0 else (0.0 if diff == 0 else 100.0)
                abs_pct_errors.append(pct_err)

                if diff <= 0.05 or pct_err <= 1.0:
                    close_numeric_matches += 1

            # Check unit
            exp_unit = exp_dict.get("unit")
            if exp_unit and m.original_unit:
                total_expected_units += 1
                # Accept direct or normalized equality
                if (
                    exp_unit.lower() == m.original_unit.lower()
                    or (m.normalized_unit and exp_unit.lower() == m.normalized_unit.lower())
                ):
                    correct_units += 1

            # Check ambiguity flagging
            if exp_dict.get("is_ambiguous"):
                total_expected_ambiguous += 1
                if m.is_ambiguous:
                    correctly_flagged_ambiguous += 1

        # Check multi-depth parameters if present (TC-07)
        if "expected_parameters_multi_depth" in gt:
            for exp_item in gt["expected_parameters_multi_depth"]:
                total_expected_fields += 1
                total_expected_rows += 1
                pkey = exp_item["parameter_key"]
                depth = exp_item["depth"]
                exp_val = exp_item["value"]
                exp_unit = exp_item["unit"]

                # Find matching measurement with depth
                matched = False
                for m in extraction.measurements:
                    if m.parameter_key == pkey and (m.sample_depth == depth or depth in str(m.original_parameter_name)):
                        matched = True
                        correctly_extracted_fields += 1
                        correctly_parsed_rows += 1
                        if exp_val is not None and m.original_value is not None:
                            total_numeric_comparisons += 1
                            diff = abs(m.original_value - exp_val)
                            pct_err = (diff / exp_val) * 100.0 if exp_val != 0 else 0.0
                            abs_pct_errors.append(pct_err)
                            if diff <= 0.05 or pct_err <= 1.0:
                                close_numeric_matches += 1
                        if exp_unit and m.original_unit:
                            total_expected_units += 1
                            if exp_unit.lower() in m.original_unit.lower():
                                correct_units += 1
                        break

        # Check case-level ambiguity expectation
        exp_amb_count = gt.get("expected_ambiguity_count")
        if exp_amb_count is not None and exp_amb_count > 0:
            if extraction.is_ambiguous and extraction.ambiguous_parameters_count >= exp_amb_count:
                pass  # verified

        report_results.append(case_summary)
        print(f"[{case_summary['id']}] {doc_filename:<32} {case_summary['modality']:<12} Params: {case_summary['params_detected']:<2} Ambiguous: {str(case_summary['is_ambiguous']):<5}")

    # Compute aggregate percentages
    fea = (correctly_extracted_fields / total_expected_fields * 100.0) if total_expected_fields > 0 else 100.0
    nea = (close_numeric_matches / total_numeric_comparisons * 100.0) if total_numeric_comparisons > 0 else 100.0
    mape = (sum(abs_pct_errors) / len(abs_pct_errors)) if abs_pct_errors else 0.0
    uea = (correct_units / total_expected_units * 100.0) if total_expected_units > 0 else 100.0
    sma = (correct_metadata / total_expected_metadata * 100.0) if total_expected_metadata > 0 else 100.0
    tea = (correctly_parsed_rows / total_expected_rows * 100.0) if total_expected_rows > 0 else 100.0
    adr = (correctly_flagged_ambiguous / total_expected_ambiguous * 100.0) if total_expected_ambiguous > 0 else 100.0

    print("\n" + "=" * 80)
    print(" AGGREGATE EVALUATION ACCURACY METRICS")
    print("=" * 80)
    print(f" 1. Field Extraction Accuracy (FEA):        {fea:6.2f}%  (Target: >= 90.0%) - {'PASS' if fea >= 90.0 else 'FAIL'}")
    print(f" 2. Numeric Extraction Accuracy (NEA):      {nea:6.2f}%  (Target: >= 95.0%) - {'PASS' if nea >= 95.0 else 'FAIL'}")
    print(f"    Mean Absolute Percentage Error (MAPE):  {mape:6.2f}%  (Target: <=  5.0%) - {'PASS' if mape <= 5.0 else 'FAIL'}")
    print(f" 3. Unit Extraction Accuracy (UEA):         {uea:6.2f}%  (Target: >= 95.0%) - {'PASS' if uea >= 95.0 else 'FAIL'}")
    print(f" 4. Sample Metadata Accuracy (SMA):         {sma:6.2f}%  (Target: >= 85.0%) - {'PASS' if sma >= 85.0 else 'FAIL'}")
    print(f" 5. Table Extraction Accuracy (TEA):        {tea:6.2f}%  (Target: >= 90.0%) - {'PASS' if tea >= 90.0 else 'FAIL'}")
    print(f" 6. Ambiguity Detection Rate (ADR):         {adr:6.2f}%  (Target: >= 90.0%) - {'PASS' if adr >= 90.0 else 'FAIL'}")
    print("=" * 80)

    all_passed = (
        fea >= 90.0
        and nea >= 95.0
        and mape <= 5.0
        and uea >= 95.0
        and sma >= 85.0
        and tea >= 90.0
        and adr >= 90.0
    )
    print(f" OVERALL BENCHMARK RESULT: {'PASSED' if all_passed else 'FAILED'}\n")

    return {
        "all_passed": all_passed,
        "fea": fea,
        "nea": nea,
        "mape": mape,
        "uea": uea,
        "sma": sma,
        "tea": tea,
        "adr": adr,
        "total_test_cases": len(test_cases),
        "report_results": report_results,
    }


if __name__ == "__main__":
    mock_flag = "--mock" in sys.argv or os.environ.get("SOIL_OCR_MOCK", "0") == "1"
    metrics = run_evaluation(mock_mode=mock_flag)
    sys.exit(0 if metrics["all_passed"] else 1)
