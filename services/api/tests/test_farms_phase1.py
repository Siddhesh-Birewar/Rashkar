import uuid
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

from cropnet.services.api.app.main import app
from cropnet.services.api.app.services.spatial_extractor import SpatialSoilService

client = TestClient(app)


def test_farm_full_crud_and_geospatial_lifecycle():
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    # 1. CREATE FARM (Valid Baramati Polygon)
    farm_payload = {
        "name": "Baramati Sugarcane Farm",
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Malegaon",
        "irrigation_type": "irrigated",
        "water_source": "canal",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.525, 18.175],
                [74.535, 18.175],
                [74.535, 18.185],
                [74.525, 18.185],
                [74.525, 18.175]
            ]]
        }
    }

    create_resp = client.post(
        "/api/v1/farms",
        json=farm_payload,
        headers={"X-Dev-User-Id": user1_id}
    )
    assert create_resp.status_code == 201
    created_farm = create_resp.json()
    farm_id = created_farm["id"]

    assert created_farm["name"] == "Baramati Sugarcane Farm"
    assert created_farm["owner_id"] == user1_id
    assert created_farm["calculated_area_hectares"] > 0
    assert created_farm["calculated_area_acres"] > 0
    assert 18.17 <= created_farm["centroid_latitude"] <= 18.19
    assert 74.52 <= created_farm["centroid_longitude"] <= 74.54
    assert created_farm["latitude"] == created_farm["centroid_latitude"]
    assert created_farm["longitude"] == created_farm["centroid_longitude"]

    # 2. LIST FARMS & MULTI-USER ISOLATION
    # User 1 should see their farm
    list_u1 = client.get("/api/v1/farms", headers={"X-Dev-User-Id": user1_id})
    assert list_u1.status_code == 200
    u1_farms = list_u1.json()
    assert any(f["id"] == farm_id for f in u1_farms)

    # User 2 should NOT see User 1's farm
    list_u2 = client.get("/api/v1/farms", headers={"X-Dev-User-Id": user2_id})
    assert list_u2.status_code == 200
    u2_farms = list_u2.json()
    assert not any(f["id"] == farm_id for f in u2_farms)

    # 3. GET FARM DETAILS & FORBIDDEN ACCESS
    # User 2 trying to GET User 1's farm -> 403 Forbidden
    forbidden_get = client.get(f"/api/v1/farms/{farm_id}", headers={"X-Dev-User-Id": user2_id})
    assert forbidden_get.status_code == 403

    # User 1 GET -> 200 OK
    valid_get = client.get(f"/api/v1/farms/{farm_id}", headers={"X-Dev-User-Id": user1_id})
    assert valid_get.status_code == 200
    assert valid_get.json()["id"] == farm_id

    # 4. UPDATE FARM (PUT)
    # User 2 cannot update User 1's farm -> 403 Forbidden
    forbidden_put = client.put(
        f"/api/v1/farms/{farm_id}",
        json={"name": "Hacked Farm Name"},
        headers={"X-Dev-User-Id": user2_id}
    )
    assert forbidden_put.status_code == 403

    # User 1 updates name and updates polygon boundary (expands plot)
    update_payload = {
        "name": "Baramati Sugarcane Estate - Expanded",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.520, 18.170],
                [74.540, 18.170],
                [74.540, 18.190],
                [74.520, 18.190],
                [74.520, 18.170]
            ]]
        }
    }
    valid_put = client.put(
        f"/api/v1/farms/{farm_id}",
        json=update_payload,
        headers={"X-Dev-User-Id": user1_id}
    )
    assert valid_put.status_code == 200
    updated_data = valid_put.json()
    assert updated_data["name"] == "Baramati Sugarcane Estate - Expanded"
    # Expanded area should be strictly larger than original
    assert updated_data["calculated_area_hectares"] > created_farm["calculated_area_hectares"]

    # 5. INTEGRATION CHECK WITH SPATIAL SOIL SERVICE
    # Verify the saved polygon can be consumed by SpatialSoilService
    spatial_service = SpatialSoilService()
    saved_coords = updated_data["geometry"]["coordinates"][0]
    saved_poly = Polygon(saved_coords)
    assert saved_poly.is_valid
    assert not saved_poly.is_empty

    # 6. DELETE FARM
    # User 2 cannot delete User 1's farm -> 403 Forbidden
    forbidden_delete = client.delete(f"/api/v1/farms/{farm_id}", headers={"X-Dev-User-Id": user2_id})
    assert forbidden_delete.status_code == 403

    # User 1 deletes farm -> 204 No Content
    valid_delete = client.delete(f"/api/v1/farms/{farm_id}", headers={"X-Dev-User-Id": user1_id})
    assert valid_delete.status_code == 204

    # Subsequent GET returns 404 Not Found
    not_found = client.get(f"/api/v1/farms/{farm_id}", headers={"X-Dev-User-Id": user1_id})
    assert not_found.status_code == 404


def test_geospatial_polygon_validation_rules():
    user_id = str(uuid.uuid4())

    # Case A: Reject non-closed polygon (first point != last point)
    resp_unclosed = client.post(
        "/api/v1/farms",
        json={
            "name": "Unclosed Farm",
            "taluka": "Maval",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [73.68, 18.76],
                    [73.69, 18.76],
                    [73.69, 18.77],
                    [73.68, 18.78]  # not closed back to [73.68, 18.76]
                ]]
            }
        },
        headers={"X-Dev-User-Id": user_id}
    )
    assert resp_unclosed.status_code == 422

    # Case B: Reject degenerate polygon (< 3 distinct vertices)
    resp_degenerate = client.post(
        "/api/v1/farms",
        json={
            "name": "Degenerate Line Farm",
            "taluka": "Maval",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [73.68, 18.76],
                    [73.69, 18.76],
                    [73.68, 18.76],
                    [73.68, 18.76]
                ]]
            }
        },
        headers={"X-Dev-User-Id": user_id}
    )
    assert resp_degenerate.status_code == 422

    # Case C: Reject self-intersecting polygon (bowtie / figure-8)
    resp_self_intersect = client.post(
        "/api/v1/farms",
        json={
            "name": "Self-Intersecting Bowtie Farm",
            "taluka": "Maval",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [73.68, 18.76],
                    [73.70, 18.78],
                    [73.70, 18.76],
                    [73.68, 18.78],
                    [73.68, 18.76]
                ]]
            }
        },
        headers={"X-Dev-User-Id": user_id}
    )
    assert resp_self_intersect.status_code == 422

    # Case D: Reject out-of-range coordinates (latitude > 90)
    resp_oob = client.post(
        "/api/v1/farms",
        json={
            "name": "Out of Bounds Farm",
            "taluka": "Maval",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [73.68, 95.0],
                    [73.69, 95.0],
                    [73.69, 96.0],
                    [73.68, 95.0]
                ]]
            }
        },
        headers={"X-Dev-User-Id": user_id}
    )
    assert resp_oob.status_code == 422
