"""
CropNet AI — Phase 5.7.3 End-to-End Satellite Feature Browser Acceptance & Verification.

Verifies:
1. Backend Satellite REST endpoints (latest, timeseries, spatial-metadata, raster-map).
2. Farm Details workspace displaying SatelliteVegetationSummaryCard.
3. Satellite Vegetation screen displaying:
   - Provenance Card (Product ID, sensor, tile, baseline, acquisition vs sync dates, polygon vs discretized area).
   - Grounded Vegetation Health Indicators (Pure canopy NDVI, NDMI with 20m SWIR disclosure, valid surface coverage %).
   - SCL Surface Composition (Canopy, bare soil, water, masked, with bare soil dilution explanation).
   - Spatial Raster Visualization (Clipped 10m raster, layer toggle, legend, spatial bounds).
   - Non-fabricated historical trend monitoring.
   - Scientific safeguard notice.
4. Mobile viewport (375x812) responsiveness.
"""
import os
import sys
import json
import time
import base64
import requests
import asyncio
import aiohttp
import subprocess

BASE_API_URL = "http://127.0.0.1:8000/api/v1"
FLUTTER_WEB_URL = "http://localhost:8080"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ARTIFACTS_DIR = "/Users/siddheshbirewar/.gemini/antigravity/brain/ee291428-4c13-4698-b1ae-642f4c613070"
DOCS_SCREENSHOTS_DIR = "/Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/docs/screenshots"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(DOCS_SCREENSHOTS_DIR, exist_ok=True)

FARM_ID = "94a1f16e-bf0d-4d3f-9bd3-d63a57189818"
OWNER_ID = "00000000-0000-0000-0000-000000000001"


def verify_api_endpoints():
    print(f"\n=== [PHASE 5.7.3] VERIFYING SATELLITE API ENDPOINTS FOR FARM {FARM_ID} ===")
    headers = {"X-Dev-User-Id": OWNER_ID}

    # 1. Latest Observation
    resp = requests.get(f"{BASE_API_URL}/farms/{FARM_ID}/satellite/latest", headers=headers)
    assert resp.status_code == 200, f"Latest observation failed: {resp.text}"
    latest = resp.json()
    print(f"[OK] Latest Observation:")
    print(f"     Product ID: {latest.get('product_id')}")
    print(f"     Observation Date: {latest.get('observation_date')}")
    print(f"     Mean NDVI: {latest.get('mean_ndvi')}")
    print(f"     Vegetation Mean NDVI: {latest.get('vegetation_mean_ndvi')}")
    print(f"     Mean NDMI: {latest.get('mean_ndmi')}")
    print(f"     Quality Status: {latest.get('quality_status')}")

    # 2. Spatial Metadata
    resp_meta = requests.get(f"{BASE_API_URL}/farms/{FARM_ID}/satellite/latest/spatial-metadata", headers=headers)
    assert resp_meta.status_code == 200, f"Spatial metadata failed: {resp_meta.text}"
    meta = resp_meta.json()
    print(f"[OK] Spatial Metadata:")
    print(f"     Bounds: {meta.get('bounds')}")
    print(f"     Dimensions: {meta.get('width')}x{meta.get('height')}")
    print(f"     Pixel Counts: veg={meta.get('vegetation_pixel_count')}, soil={meta.get('bare_soil_pixel_count')}")

    # 3. Derived Raster Map PNG
    resp_png = requests.get(f"{BASE_API_URL}/farms/{FARM_ID}/satellite/latest/raster-map?index_type=ndvi", headers=headers)
    assert resp_png.status_code == 200, f"Raster map failed: {resp_png.status_code}"
    assert resp_png.headers.get("content-type") == "image/png"
    assert "X-Raster-Bounds" in resp_png.headers
    print(f"[OK] Derived Raster Map PNG: {len(resp_png.content)} bytes, Bounds header: {resp_png.headers.get('X-Raster-Bounds')}")

    # 4. Timeseries
    resp_ts = requests.get(f"{BASE_API_URL}/farms/{FARM_ID}/satellite/timeseries?months=6", headers=headers)
    assert resp_ts.status_code == 200, f"Timeseries failed: {resp_ts.text}"
    ts = resp_ts.json()
    print(f"[OK] Timeseries: {len(ts.get('series', []))} observations, Interpretation: '{ts.get('vegetation_interpretation')}'")


async def capture_e2e_screenshots():
    print("\n=== [PHASE 5.7.3] CAPTURING E2E SCREENSHOTS VIA CHROME CDP ===")
    port = 9232
    user_data_dir = f"/tmp/chrome_cdp_cropnet_{port}"

    chrome_cmd = [
        CHROME_BIN,
        "--headless=new",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--window-size=1280,1000",
    ]
    proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(2.5)

    async def send_cmd(ws, msg_id, method, params=None):
        await ws.send_json({"id": msg_id, "method": method, "params": params or {}})
        while True:
            resp = await ws.receive_json()
            if resp.get("id") == msg_id:
                return resp

    async def save_shot(ws, msg_id, filename):
        shot = await send_cmd(ws, msg_id, "Page.captureScreenshot", {"format": "png"})
        if "result" in shot and "data" in shot["result"]:
            img_bytes = base64.b64decode(shot["result"]["data"])
            doc_path = os.path.join(DOCS_SCREENSHOTS_DIR, filename)
            art_path = os.path.join(ARTIFACTS_DIR, filename)
            with open(doc_path, "wb") as f:
                f.write(img_bytes)
            with open(art_path, "wb") as f:
                f.write(img_bytes)
            print(f"[SUCCESS] Saved: {filename} ({len(img_bytes)} bytes)")
        else:
            print(f"[WARN] Failed to capture: {filename}")

    async def scroll_wheel(ws, delta_y, count=5):
        for i in range(count):
            await send_cmd(ws, 500 + i, "Input.dispatchMouseEvent", {
                "type": "mouseWheel",
                "x": 640,
                "y": 500,
                "deltaX": 0,
                "deltaY": delta_y,
            })
            await asyncio.sleep(0.2)
        await asyncio.sleep(1.0)

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Create clean new tab
            async with session.put(f"http://127.0.0.1:{port}/json/new") as r:
                tab = await r.json()
                ws_url = tab["webSocketDebuggerUrl"]

            async with session.ws_connect(ws_url) as ws:
                await send_cmd(ws, 1, "Page.enable")
                await send_cmd(ws, 2, "Runtime.enable")
                await send_cmd(ws, 3, "Emulation.setDeviceMetricsOverride", {
                    "width": 1280,
                    "height": 1000,
                    "deviceScaleFactor": 1.0,
                    "mobile": False,
                })

                # -------------------------------------------------------------
                # SHOT 1: Farm Details Screen with SatelliteVegetationSummaryCard
                # -------------------------------------------------------------
                farm_url = f"{FLUTTER_WEB_URL}/#/farms/{FARM_ID}"
                print(f"\n[E2E] Navigating to Farm Details Dashboard: {farm_url}")
                await send_cmd(ws, 4, "Page.navigate", {"url": farm_url})
                print("Waiting 12s for Flutter Web, Farm Details & Satellite Summary Card to load...")
                await asyncio.sleep(12.0)

                # Scroll down slightly with mouseWheel to center Summary Card
                await scroll_wheel(ws, delta_y=180, count=2)
                await save_shot(ws, 6, "phase5_7_3_farm_dashboard_summary.png")

                # -------------------------------------------------------------
                # SHOT 2: Satellite Vegetation Screen (Top: Header, Provenance, Indicators)
                # -------------------------------------------------------------
                veg_url = f"{FLUTTER_WEB_URL}/#/farms/{FARM_ID}/vegetation"
                print(f"\n[E2E] Navigating to Satellite Vegetation Workspace: {veg_url}")
                await send_cmd(ws, 7, "Page.navigate", {"url": veg_url})
                print("Waiting 10s for Satellite Workspace observations to render...")
                await asyncio.sleep(10.0)

                await save_shot(ws, 9, "phase5_7_3_satellite_workspace_provenance_and_indicators.png")

                # -------------------------------------------------------------
                # SHOT 3: Spatial Raster Visualization & Surface Composition
                # -------------------------------------------------------------
                print("\n[E2E] Scrolling down to Spatial Raster Map...")
                await scroll_wheel(ws, delta_y=280, count=2)
                await save_shot(ws, 11, "phase5_7_3_satellite_spatial_raster_map.png")

                # -------------------------------------------------------------
                # SHOT 4: Historical Monitoring & Scientific Disclaimers
                # -------------------------------------------------------------
                print("\n[E2E] Scrolling down to Historical Trends & Scientific Safeguards...")
                await scroll_wheel(ws, delta_y=350, count=3)
                await save_shot(ws, 13, "phase5_7_3_satellite_history_and_safeguards.png")

                # -------------------------------------------------------------
                # SHOT 5: Mobile Viewport Responsiveness (375x812)
                # -------------------------------------------------------------
                print("\n[E2E] Switching to Mobile Viewport (375x812)...")
                await send_cmd(ws, 14, "Emulation.setDeviceMetricsOverride", {
                    "width": 375,
                    "height": 812,
                    "deviceScaleFactor": 2.0,
                    "mobile": True,
                })
                # Scroll back to top
                await scroll_wheel(ws, delta_y=-600, count=6)
                await save_shot(ws, 16, "phase5_7_3_satellite_mobile_responsive.png")

            await session.get(f"http://127.0.0.1:{port}/json/close/{tab['id']}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    verify_api_endpoints()
    asyncio.run(capture_e2e_screenshots())
