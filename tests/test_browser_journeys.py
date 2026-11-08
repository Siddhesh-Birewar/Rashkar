import os
import pytest
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://127.0.0.1:8080"
BACKEND_HEALTH_URL = "http://127.0.0.1:8000/v1/health"
SCREENSHOT_DIR = "docs/screenshots"

def setup_module():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def test_backend_reachable_and_healthy():
    with sync_playwright() as p:
        request_context = p.request.new_context()
        response = request_context.get(BACKEND_HEALTH_URL)
        assert response.status == 200, f"Backend returned {response.status}"
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Rashkar Climate-Smart Agriculture Platform"

def test_flutter_web_serves_html_and_assets():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        response = page.goto(FRONTEND_URL, wait_until="domcontentloaded")
        assert response.status == 200, f"Expected 200 from web server, got {response.status}"
        
        # Verify title and meta elements
        assert "Rashkar" in page.title() or "rashkar" in page.content().lower()

        browser.close()

def test_responsive_viewports_and_screenshots():
    viewports = [
        {"name": "desktop_1440x900", "width": 1440, "height": 900},
        {"name": "laptop_1024x768", "width": 1024, "height": 768},
        {"name": "tablet_768x1024", "width": 768, "height": 1024},
        {"name": "mobile_390x844", "width": 390, "height": 844},
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for vp in viewports:
            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()
            
            page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
            
            # Wait for flutter bootstrap / canvas
            page.wait_for_timeout(3000)
            
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"viewport_{vp['name']}.png")
            page.screenshot(path=screenshot_path)
            assert os.path.exists(screenshot_path)
            assert os.path.getsize(screenshot_path) > 1000
            
            context.close()
            
        browser.close()

def test_browser_api_data_fetch():
    """Verify browser page can query FastAPI endpoints directly with CORS headers."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(FRONTEND_URL, wait_until="domcontentloaded")
        
        # Execute fetch directly within browser window
        summary_result = page.evaluate("""async () => {
            const res = await fetch('http://127.0.0.1:8000/v1/farms/farm_demo_pune_01/summary');
            return {
                status: res.status,
                data: await res.json()
            };
        }""")
        
        assert summary_result["status"] == 200
        summary_data = summary_result["data"]
        assert summary_data["farmer_name"] == "Ramesh Patil"
        assert summary_data["active_crop_code"] == "soybean"
        assert "weather_summary" in summary_data
        assert "soil_summary" in summary_data
        
        browser.close()

def test_browser_edit_profile_lifecycle():
    """Verify complete profile editing lifecycle from browser environment."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(FRONTEND_URL, wait_until="domcontentloaded")

        result = page.evaluate("""async () => {
            // 1. Register a new farm
            const regPayload = {
                farmer_name: "Kisan Rao",
                phone_number: "+919988776655",
                district: "Pune",
                taluka: "Baramati",
                village: "Malegaon",
                total_area_acres: 3.5,
                boundary_geojson: {
                    type: "Polygon",
                    coordinates: [[[74.55, 18.15], [74.56, 18.15], [74.56, 18.16], [74.55, 18.16], [74.55, 18.15]]]
                },
                crop_code: "soybean",
                sowing_date: "2026-06-15",
                irrigation_source: "canal"
            };
            const regRes = await fetch('http://127.0.0.1:8000/v1/farms/guided-registration', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(regPayload)
            });
            const regData = await regRes.json();
            const farmId = regData.farm_id;

            // 2. Edit Profile
            const updatePayload = {
                farmer_name: "Kisan Rao Updated",
                phone_number: "+919988776655",
                district: "Nashik",
                taluka: "Niphad",
                village: "Pimpalgaon",
                total_area_acres: 6.0,
                centroid_lat: 20.08,
                centroid_lon: 74.02,
                boundary_geojson: {
                    type: "Polygon",
                    coordinates: [[[74.01, 20.07], [74.03, 20.07], [74.03, 20.09], [74.01, 20.09], [74.01, 20.07]]]
                },
                crop_code: "onion",
                sowing_date: "2026-08-01",
                irrigation_source: "drip"
            };
            const putRes = await fetch(`http://127.0.0.1:8000/v1/farms/${farmId}/profile`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(updatePayload)
            });
            const putData = await putRes.json();

            // 3. Fetch recalculated summary
            const sumRes = await fetch(`http://127.0.0.1:8000/v1/farms/${farmId}/summary`);
            const sumData = await sumRes.json();

            // 4. Fetch recalculated yield intelligence
            const yieldRes = await fetch(`http://127.0.0.1:8000/v1/yield-intelligence/${farmId}/yield-risk`);
            const yieldData = await yieldRes.json();

            return {
                farmId,
                regStatus: regRes.status,
                putStatus: putRes.status,
                putData,
                sumData,
                yieldData
            };
        }""")

        assert result["regStatus"] == 200
        assert result["putStatus"] == 200
        assert result["putData"]["farmer_name"] == "Kisan Rao Updated"
        assert result["putData"]["active_crop_code"] == "onion"
        assert "Nashik" in result["sumData"]["location_display"]
        assert "Niphad" in result["sumData"]["location_display"]
        assert result["sumData"]["total_area_acres"] == 6.0
        assert result["yieldData"]["crop_code"] == "onion"
        assert "yield_baseline" in result["yieldData"]

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "profile_edit_lifecycle.png"))
        browser.close()

