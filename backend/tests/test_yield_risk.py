from datetime import date

def test_yield_risk_end_to_end(client):
    # 1. Create a farm in Baramati, Pune
    farm_res = client.post("/v1/farms/", json={
        "owner_id": "farmer_baramati_01",
        "farm_name": "Kisan Seva Krishi Plot",
        "district": "Pune",
        "taluka": "Baramati",
        "village": "Malegaon",
        "latitude": 18.1512,
        "longitude": 74.5768
    })
    assert farm_res.status_code == 200
    farm_id = farm_res.json()["farm_id"]

    # 2. Add plot
    plot_res = client.post(f"/v1/farms/{farm_id}/plots", json={
        "plot_name": "Plot 1 - North",
        "area_acres": 3.0,
        "irrigation_type": "canal"
    })
    assert plot_res.status_code == 200
    plot_id = plot_res.json()["plot_id"]

    # 3. Add Crop Cycle (Soybean sown 45 days ago)
    cycle_res = client.post(f"/v1/farms/{farm_id}/crop-cycles?plot_id={plot_id}", json={
        "crop_code": "soybean",
        "variety_name": "JS-335",
        "season": "kharif",
        "sowing_date": "2024-06-25",
        "farmer_confirmed_stage": "R1_FLOWERING"
    })
    assert cycle_res.status_code == 200

    # 4. Assess Yield Risk
    risk_res = client.get(f"/v1/yield-intelligence/{farm_id}/yield-risk?plot_id={plot_id}")
    assert risk_res.status_code == 200
    data = risk_res.json()

    # Assertions on response structure
    assert data["farm_id"] == farm_id
    assert data["crop_code"] == "soybean"
    assert data["coverage"]["crop_status"] == "supported_rules_and_baselines"

    # Stage estimation
    assert data["crop_stage"]["stage_code"] == "R1_FLOWERING"
    assert data["crop_stage"]["farmer_confirmed"] is True

    # Multi-dimensional risks present
    dimensions = [r["risk_dimension"] for r in data["risks"]]
    assert "weather_dry_spell" in dimensions
    assert "excess_rainfall_waterlogging" in dimensions
    assert "soil_constraint" in dimensions
    assert "pest_disease_watch" in dimensions

    # District yield baseline present
    assert "yield_baseline" in data
    assert data["yield_baseline"]["status"] == "district_historical_baseline"
    assert data["yield_baseline"]["historical_mean_t_ha"] is not None
    assert "Plot-level numerical prediction is disabled" in data["yield_baseline"]["disclaimer"]
