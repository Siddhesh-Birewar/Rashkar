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
