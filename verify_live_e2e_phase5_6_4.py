"""
Live End-to-End Integration Verification against running FastAPI backend on http://127.0.0.1:8000.
Executes all Phase 5.6.4 acceptance criteria over real HTTP networking:
1. Creates dedicated QA test farm
2. Establishes ISRIC SoilGrids 2.0 spatial baseline
3. Uploads genuine lag_sample.pdf via multipart/form-data
4. Verifies OCR extraction (8 parameters, 2 samples, UW Lab metadata, elemental P/K ppm, % OM)
5. Confirms human-in-the-loop review
6. Verifies canonical fused soil profile (precedence, dual-source preservation, unknown depth)
7. Evaluates agricultural advisory before & after confirmation
8. Proves cross-farm isolation with an independent reference farm
"""
import sys
import json
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
PDF_PATH = "/Users/siddheshbirewar/Downloads/lag_sample.pdf"

def main():
    print("=== STARTING PHASE 5.6.4 LIVE HTTP VERIFICATION ===")
    user_id = str(uuid.uuid4())
    headers = {"X-Dev-User-Id": user_id}

    # 1. Create QA Test Farm
    farm_payload = {
        "name": "QA Wisconsin Soil Lab Test Facility",
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "QA_Station",
        "irrigation_type": "irrigated",
        "water_source": "canal",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.528, 18.178],
                [74.532, 18.178],
                [74.532, 18.182],
                [74.528, 18.182],
                [74.528, 18.178]
            ]]
        }
    }
    r = requests.post(f"{BASE_URL}/farms", json=farm_payload, headers=headers)
    assert r.status_code == 201, f"Create QA farm failed: {r.text}"
    qa_farm = r.json()
    qa_farm_id = qa_farm["id"]
    print(f"[OK] 1. Created QA Farm: ID={qa_farm_id}, Name='{qa_farm['name']}'")

    # 1b. Create Reference Farm B for Cross-Farm Isolation Test
    user_b = str(uuid.uuid4())
    r_b = requests.post(f"{BASE_URL}/farms", json={
        "name": "Baramati Production Reference Farm B",
        "taluka": "Indapur",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Nimgaon",
        "irrigation_type": "irrigated",
        "water_source": "well",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[74.910, 18.150], [74.915, 18.150], [74.915, 18.155], [74.910, 18.155], [74.910, 18.150]]]
        }
    }, headers={"X-Dev-User-Id": user_b})
    assert r_b.status_code == 201
    ref_farm_id = r_b.json()["id"]
    print(f"[OK] 1b. Created Isolation Reference Farm B: ID={ref_farm_id}")

    # 2. Establish SoilGrids Baseline
    r = requests.post(f"{BASE_URL}/farms/{qa_farm_id}/soil/analyse", json={"depth": "0-5cm"}, headers=headers)
    assert r.status_code == 200, f"Analyse failed: {r.text}"
    baseline_profile = r.json()
    baseline_ph = baseline_profile["ph"]["value"]
    print(f"[OK] 2. Established SoilGrids Baseline Profile (version={baseline_profile['version']}, baseline_ph={baseline_ph})")

    # Also establish baseline for Reference Farm B
    requests.post(f"{BASE_URL}/farms/{ref_farm_id}/soil/analyse", json={"depth": "0-5cm"}, headers={"X-Dev-User-Id": user_b})

    # 3. Pre-Confirmation Advisory Evaluation (should reflect GEOSPATIAL provenance)
    r = requests.post(f"{BASE_URL}/farms/{qa_farm_id}/advisory/evaluate", json={"target_season": "kharif"}, headers=headers)
    assert r.status_code == 200, f"Pre-eval failed: {r.text}"
    pre_eval = r.json()
    pre_prov = pre_eval["farm_context"]["soil_data_provenance"]
    print(f"[OK] 3. Pre-Confirmation Evaluation: provenance='{pre_prov}', crop_outcomes={len(pre_eval['crop_outcomes'])}")

    # 4. Upload genuine lag_sample.pdf
    with open(PDF_PATH, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("lag_sample.pdf", file_bytes, "application/pdf")}
    data = {
        "laboratory_name": "UW Soil & Plant Analysis Lab",
        "sample_depth_interval": "Not specified",
        "depth_provenance": "UNKNOWN",
    }
    r = requests.post(f"{BASE_URL}/farms/{qa_farm_id}/soil-reports/upload", files=files, data=data, headers=headers)
    assert r.status_code == 201, f"Upload failed: {r.text}"
    report = r.json()
    report_id = report["id"]
    measurements = report["measurements"]
    print(f"[OK] 4. Uploaded lag_sample.pdf: report_id={report_id}, status='{report['extraction_status']}', measurements_count={len(measurements)}")
    assert len(measurements) == 8, f"Expected 8 measurements, got {len(measurements)}"
    assert report["laboratory_name"] == "UW Soil & Plant Analysis Lab"
    assert report["lab_number"] == "54321"
    assert report["date_received"].startswith("2007-08-01")
    assert report["date_processed"].startswith("2007-08-10")
    assert report["sample_collection_date"] is None
    assert report["sample_depth_interval"] in [None, "Not specified"]
    assert report["depth_provenance"] == "UNKNOWN"

    # 5. Strict Isolation: Profile MUST NOT contain lab values prior to confirmation
    r = requests.get(f"{BASE_URL}/farms/{qa_farm_id}/soil", headers=headers)
    assert r.status_code == 200
    pre_conf_soil = r.json()
    assert pre_conf_soil["ph"]["verification_status"] == "map_derived_estimate"
    assert "phosphorus" not in pre_conf_soil.get("additional_parameters", {})
    print("[OK] 5. Verified Strict Isolation: Unconfirmed report has NOT altered canonical profile")

    # 6. Confirm Human-in-the-Loop Review
    r = requests.post(f"{BASE_URL}/farms/{qa_farm_id}/soil-reports/{report_id}/confirm", json={}, headers=headers)
    assert r.status_code == 200, f"Confirm failed: {r.text}"
    conf = r.json()
    print(f"[OK] 6. Confirmed Report: status='{conf['status']}', confirmed_count={conf['confirmed_measurement_count']}")
    assert conf["confirmed_measurement_count"] == 8

    # 7. Verify Canonical Fused Soil Profile
    r = requests.get(f"{BASE_URL}/farms/{qa_farm_id}/soil", headers=headers)
    assert r.status_code == 200
    fused = r.json()
    assert fused["ph"]["verification_status"] == "laboratory_verified"
    assert "UW Soil & Plant Analysis Lab" in fused["ph"]["source"]
    assert fused["ph"]["depth_interval"] == "Not specified"
    assert "isric_ph" in fused["additional_parameters"]
    assert fused["additional_parameters"]["isric_ph"]["verification_status"] == "map_derived_estimate"
    assert "phosphorus" in fused["additional_parameters"]
    assert fused["additional_parameters"]["phosphorus"]["unit"] == "ppm"
    assert "potassium" in fused["additional_parameters"]
    assert fused["additional_parameters"]["potassium"]["unit"] == "ppm"
    assert "organic_matter" in fused["additional_parameters"]
    assert fused["available_nitrogen"]["value"] is None
    assert fused["available_phosphorus"]["value"] is None
    assert fused["available_potassium"]["value"] is None
    print(f"[OK] 7. Canonical Soil Profile Fused: pH={fused['ph']['value']} (Lab Verified), isric_ph={fused['additional_parameters']['isric_ph']['value']} (ISRIC Preserved), P={fused['additional_parameters']['phosphorus']['value']} ppm, K={fused['additional_parameters']['potassium']['value']} ppm, OM={fused['additional_parameters']['organic_matter']['value']} %")

    # 8. Post-Confirmation Advisory Evaluation
    r = requests.post(f"{BASE_URL}/farms/{qa_farm_id}/advisory/evaluate", json={"target_season": "kharif"}, headers=headers)
    assert r.status_code == 200
    post_eval = r.json()
    post_prov = post_eval["farm_context"]["soil_data_provenance"]
    print(f"[OK] 8. Post-Confirmation Evaluation: provenance='{post_prov}', crop_outcomes={len(post_eval['crop_outcomes'])}")
    assert post_prov == "laboratory_measured"

    # 9. Cross-Farm Isolation: Reference Farm B MUST remain pure geospatial
    r = requests.get(f"{BASE_URL}/farms/{ref_farm_id}/soil", headers={"X-Dev-User-Id": user_b})
    assert r.status_code == 200
    ref_soil = r.json()
    assert ref_soil["ph"]["verification_status"] == "map_derived_estimate"
    assert "isric_ph" not in ref_soil.get("additional_parameters", {})
    assert "phosphorus" not in ref_soil.get("additional_parameters", {})
    print(f"[OK] 9. Cross-Farm Isolation Verified: Farm B pH status='{ref_soil['ph']['verification_status']}', 0 lab measurements leaked")

    print("\n=== ALL LIVE END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY ===")
    return {
        "qa_farm_id": qa_farm_id,
        "ref_farm_id": ref_farm_id,
        "report_id": report_id,
        "fused_profile_id": fused["profile_id"],
        "measurements_count": len(measurements),
        "post_prov": post_prov
    }

if __name__ == "__main__":
    res = main()
    print(json.dumps(res, indent=2))
