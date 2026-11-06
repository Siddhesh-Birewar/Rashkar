import pytest
from fastapi.testclient import TestClient

from cropnet.services.api.app.main import app

client = TestClient(app)


def test_registered_sources_provenance():
    """
    Verify Phase 4.1 registered sources:
    - MPKV Research Recommendations 2023 (13 pp., not full PoP)
    - ICRISAT Chickpea Manual 2010 (28 pp.)
    - ICAR-NRCP & MANAGE Pomegranate Practices 2022 (119 pp.)
    - ICAR-IISR at a Glance (8 pp. brochure, unverified_bibliographic)
    """
    # Test pomegranate sources endpoint
    res_pom = client.get("/api/v1/crops/pomegranate/sources")
    assert res_pom.status_code == 200
    pom_sources = res_pom.json()
    assert len(pom_sources) >= 1
    pom_src = pom_sources[0]
    assert pom_src["id"] == "icar_nrcp_manage_2022"
    assert "MANAGE" in pom_src["organization"]
    assert "978-93-91668-12-9" in pom_src["document_url_or_ref"]
    assert pom_src["evidence_quality"] == "verified_authoritative"

    # Test chickpea sources endpoint
    res_chk = client.get("/api/v1/crops/chickpea/sources")
    assert res_chk.status_code == 200
    chk_sources = res_chk.json()
    assert len(chk_sources) >= 1
    chk_src = chk_sources[0]
    assert chk_src["id"] == "icrisat_chickpea_2010"
    assert "ICRISAT" in chk_src["organization"]
    assert "Gaur et al." in chk_src["document_url_or_ref"]
    assert chk_src["evidence_quality"] == "verified_authoritative"


def test_pomegranate_verified_corrections():
    """
    Verify Pomegranate corrections:
    1. Optimum pH: 6.5–7.0
    2. Tolerable max pH: 8.5
    3. Tolerable min pH: None (unverified, do not fabricate 6.0)
    4. Unverified parameters contains ph_tolerable_min
    5. Universal mm annual water requirement removed (None)
    6. Daily tree water table (L/tree/day) by age and Bahar exists
    7. Regional suitability in Maval/Mulshi marked requires_regional_validation
    """
    res = client.get("/api/v1/crops/pomegranate")
    assert res.status_code == 200
    pom = res.json()

    # Soil pH assertions
    soil = pom["soil"]
    assert soil["ph_optimum_min"] == 6.5
    assert soil["ph_optimum_max"] == 7.0
    assert soil["ph_tolerable_max"] == 8.5
    assert soil["ph_tolerable_min"] is None  # Must NOT be 6.0 or 5.5
    assert "ph_tolerable_min" in (soil["unverified_parameters"] or [])
    assert soil["evidence_status"] == "verified_authoritative"

    # Water requirements assertions
    water = pom["water"]
    assert water["annual_water_requirement_mm_min"] is None
    assert water["annual_water_requirement_mm_max"] is None
    assert water["daily_water_table"] is not None
    dwt = water["daily_water_table"]
    assert dwt["unit"] == "liters_per_tree_per_day"
    assert "pp. 45–46" in dwt["citation"]

    # Validate Table 1 (Mirg Bahar) representative source entries
    mrig = dwt["mrig_bahar"]
    assert len(mrig["schedule"]) == 32
    assert mrig["schedule"][0]["mw"] == 23
    assert mrig["schedule"][0]["year_1"] == 3
    assert mrig["schedule"][0]["year_5"] == 11
    mw43 = next(s for s in mrig["schedule"] if s["mw"] == 43)
    assert mw43["year_1"] == 3
    assert mw43["year_5"] == 34

    # Validate Table 2 (Hasta Bahar) representative source entries
    hasta = dwt["hasta_bahar"]
    assert len(hasta["schedule"]) == 32
    assert hasta["schedule"][0]["mw"] == 36
    assert hasta["schedule"][0]["year_1"] == 2
    assert hasta["schedule"][0]["year_5"] == 6
    mw15 = next(s for s in hasta["schedule"] if s["mw"] == 15)
    assert mw15["year_1"] == 6
    assert mw15["year_5"] == 54

    # Validate Table 3 (Ambia Bahar) representative source entries
    ambia = dwt["ambia_bahar"]
    assert len(ambia["schedule"]) == 32
    assert ambia["schedule"][0]["mw"] == 1
    assert ambia["schedule"][0]["year_1"] == 2
    assert ambia["schedule"][0]["year_5"] == 6
    mw18 = next(s for s in ambia["schedule"] if s["mw"] == 18)
    assert mw18["year_1"] == 6
    assert mw18["year_5"] == 70

    assert water["evidence_status"] == "verified_authoritative"

    # Regional suitability
    reg = {r["taluka"]: r for r in pom["regional_suitability"]}
    assert reg["Baramati"]["evidence_status"] == "regional_screening"
    assert reg["Indapur"]["evidence_status"] == "regional_screening"
    assert reg["Maval"]["evidence_status"] == "requires_regional_validation"
    assert reg["Mulshi"]["evidence_status"] == "requires_regional_validation"
    assert "bacterial blight" in reg["Maval"]["agronomic_rationale"].lower()


def test_chickpea_verified_corrections():
    """
    Verify Chickpea corrections:
    1. Optimum pH: 6.0–8.0 (ICRISAT 2010 p. 8)
    2. Lower tolerable pH: None (marked unverified)
    3. Temperature tolerable max: 35.0 C (ICRISAT 2010 p. 3)
    4. Critical growth stages: Branching and pod filling
    5. Two separate irrigation statements (ICRISAT phenological vs MPKV 2023 Vertisol canal)
    6. Regional suitability: Baramati/Indapur verified_regional_evidence; Maval/Mulshi requires_regional_validation
    """
    res = client.get("/api/v1/crops/chickpea")
    assert res.status_code == 200
    chk = res.json()

    # Soil assertions
    soil = chk["soil"]
    assert soil["ph_optimum_min"] == 6.0
    assert soil["ph_optimum_max"] == 8.0
    assert soil["ph_tolerable_min"] is None
    assert "ph_tolerable_min" in (soil["unverified_parameters"] or [])
    assert soil["evidence_status"] == "verified_authoritative"

    # Climate assertions
    clim = chk["climate"]
    assert clim["temp_optimum_min_c"] == 15.0
    assert clim["temp_optimum_max_c"] == 25.0
    assert clim["temp_tolerable_max_c"] == 35.0
    assert "reproductive" in clim["heat_sensitivity"].lower()
    assert "flower drop" in clim["heat_sensitivity"].lower()
    assert clim["evidence_status"] == "verified_authoritative"

    # Water assertions
    water = chk["water"]
    assert "Branching stage" in water["critical_growth_stages"]
    assert "Pod filling stage" in water["critical_growth_stages"]
    assert water["irrigation_stages_detail"] is not None
    details = water["irrigation_stages_detail"]
    assert len(details) == 2
    sources = [d["source_id"] for d in details]
    assert "icrisat_chickpea_2010" in sources
    assert "mpkv_research_2023" in sources

    # Regional assertions
    reg = {r["taluka"]: r for r in chk["regional_suitability"]}
    assert reg["Baramati"]["evidence_status"] == "regional_screening"
    assert reg["Indapur"]["evidence_status"] == "regional_screening"
    assert "vertisol" in reg["Baramati"]["agronomic_rationale"].lower()
    assert reg["Maval"]["evidence_status"] == "requires_regional_validation"
    assert reg["Mulshi"]["evidence_status"] == "requires_regional_validation"


def test_regional_suitability_across_all_40_records():
    """
    Verify all 10 crops have 4 taluka records with explicit evidence_status:
    - verified_regional_evidence
    - regional_screening
    - requires_regional_validation
    No unverified categorical assertions should lack evidence provenance.
    """
    res = client.get("/api/v1/crops")
    assert res.status_code == 200
    crops = res.json()
    assert len(crops) >= 10

    total_regional_records = 0
    valid_statuses = {"verified_regional_evidence", "regional_screening", "requires_regional_validation"}

    for c in crops:
        crop_res = client.get(f"/api/v1/crops/{c['id']}")
        assert crop_res.status_code == 200
        crop_data = crop_res.json()
        reg_records = crop_data["regional_suitability"]
        assert len(reg_records) == 4, f"Crop {c['id']} must have exactly 4 pilot talukas"
        total_regional_records += len(reg_records)

        for r in reg_records:
            assert r["evidence_status"] in valid_statuses, f"Invalid evidence_status in {c['id']}/{r['taluka']}"
            if r["taluka"] in ["Baramati", "Indapur"]:
                assert r["evidence_status"] == "regional_screening", f"{c['id']} {r['taluka']} must be regional_screening"
            elif r["taluka"] in ["Maval", "Mulshi"]:
                assert r["evidence_status"] == "requires_regional_validation", f"{c['id']} {r['taluka']} must be requires_regional_validation"

    assert total_regional_records == 40


def test_crop_requirements_endpoint_supports_new_fields():
    """
    Verify GET /api/v1/crops/{crop_id}/requirements returns the new provenance and water table fields.
    """
    res = client.get("/api/v1/crops/pomegranate/requirements")
    assert res.status_code == 200
    data = res.json()
    assert data["soil"]["evidence_status"] == "verified_authoritative"
    assert data["water"]["daily_water_table"] is not None
    assert data["water"]["annual_water_requirement_mm_min"] is None
