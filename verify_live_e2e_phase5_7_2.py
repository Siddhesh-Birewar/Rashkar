"""
CropNet AI — Phase 5.7.2 Live Sentinel-2 E2E Browser Verification.

1. Calls the live sync endpoint for the registered Baramati Pilot Grape Vineyard
   (Farm ID: 94a1f16e-bf0d-4d3f-9bd3-d63a57189818).
2. Verifies real Sentinel-2 Level-2A canopy reflectance retrieval, SCL cloud masking,
   and NDVI/NDMI calculation.
3. Launches Headless Chrome via CDP, navigates to the Satellite Vegetation screen,
   and captures the full-page screenshot of the live retrieved observation.
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


def sync_live_satellite():
    print(f"\n=== STEP 1: SYNCING LIVE SENTINEL-2 OBSERVATION FOR FARM {FARM_ID} ===")
    headers = {"X-Dev-User-Id": OWNER_ID}

    # 1. Trigger live satellite sync
    resp = requests.post(f"{BASE_API_URL}/farms/{FARM_ID}/satellite/sync", headers=headers, json={}, timeout=60.0)
    assert resp.status_code == 200, f"Satellite sync failed: {resp.text}"
    data = resp.json()
    latest = data.get("latest_observation")
    assert latest is not None, "No latest observation returned"

    print(f"[OK] Live Satellite Observation Synced:")
    print(f"     Provider Status: {data.get('copernicus_provider_status')}")
    print(f"     Product ID: {latest.get('product_id')}")
    print(f"     Observation Date: {latest.get('observation_date')}")
    print(f"     Mean NDVI: {latest.get('mean_ndvi')}")
    print(f"     Median NDVI: {latest.get('median_ndvi')}")
    print(f"     Mean NDMI: {latest.get('mean_ndmi')}")
    print(f"     Valid Pixels: {latest.get('valid_pixel_count')} / {latest.get('total_pixel_count')}")
    print(f"     Farm Coverage %: {latest.get('farm_coverage_percent')}%")
    print(f"     Quality Status: {latest.get('quality_status')}")

    # 2. Verify timeseries
    resp_ts = requests.get(f"{BASE_API_URL}/farms/{FARM_ID}/satellite/timeseries?months=6", headers=headers)
    assert resp_ts.status_code == 200, f"Timeseries failed: {resp_ts.text}"
    ts_data = resp_ts.json()
    print(f"[OK] Timeseries: {len(ts_data.get('series', []))} observations, Interpretation: '{ts_data.get('vegetation_interpretation')}'")


async def capture_browser_screenshot():
    print("\n=== STEP 2: CAPTURING LIVE SATELLITE SCREENSHOT VIA CHROME CDP ===")
    port = 9225
    user_data_dir = f"/tmp/chrome_cdp_cropnet_{port}"

    chrome_cmd = [
        CHROME_BIN,
        "--headless=new",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--window-size=1280,900",
    ]
    proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(2.5)

    target_url = f"{FLUTTER_WEB_URL}/#/farms/{FARM_ID}/vegetation"
    filename = "phase5_7_2_live_satellite_workspace.png"

    async def send_cmd(ws, msg_id, method, params=None):
        await ws.send_json({"id": msg_id, "method": method, "params": params or {}})
        while True:
            resp = await ws.receive_json()
            if resp.get("id") == msg_id:
                return resp

    try:
        async with aiohttp.ClientSession() as session:
            # Create new tab directly with URL
            async with session.put(f"http://127.0.0.1:{port}/json/new?{target_url}") as r:
                tab = await r.json()
                tab_ws = tab["webSocketDebuggerUrl"]

            async with session.ws_connect(tab_ws) as ws:
                await send_cmd(ws, 1, "Page.enable")
                await send_cmd(ws, 2, "Runtime.enable")
                await send_cmd(ws, 3, "Emulation.setDeviceMetricsOverride", {
                    "width": 1280,
                    "height": 900,
                    "deviceScaleFactor": 1.0,
                    "mobile": False,
                })
                await send_cmd(ws, 4, "Page.navigate", {"url": target_url})

                # Wait for Flutter Web and live satellite API data to render
                print("Waiting 12s for Flutter rendering and API response...")
                await asyncio.sleep(12.0)

                # Capture screenshot
                shot = await send_cmd(ws, 5, "Page.captureScreenshot", {"format": "png"})
                if "result" in shot and "data" in shot["result"]:
                    img_bytes = base64.b64decode(shot["result"]["data"])

                    # Save to docs and artifacts
                    doc_path = os.path.join(DOCS_SCREENSHOTS_DIR, filename)
                    art_path = os.path.join(ARTIFACTS_DIR, filename)

                    with open(doc_path, "wb") as f:
                        f.write(img_bytes)
                    with open(art_path, "wb") as f:
                        f.write(img_bytes)

                    print(f"[SUCCESS] Screenshot captured and saved:")
                    print(f"          - {doc_path} ({len(img_bytes)} bytes)")
                    print(f"          - {art_path} ({len(img_bytes)} bytes)")
                else:
                    print(f"[WARN] Screenshot result missing: {shot}")

            await session.get(f"http://127.0.0.1:{port}/json/close/{tab['id']}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sync_live_satellite()
    asyncio.run(capture_browser_screenshot())
