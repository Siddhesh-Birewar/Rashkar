"""
CropNet AI — Phase 6.1 Screenshot Capture via Chrome DevTools Protocol (CDP).

Captures:
1. phase6_1_farm_health_dashboard_desktop.png (Unified Farm Health Dashboard - Desktop 1280x1000)
2. phase6_1_farm_health_dashboard_mobile.png (Unified Farm Health Dashboard - Mobile 390x844)
3. phase6_1_offline_resilience_banner.png (Unified Farm Health Dashboard - Cached Offline Banner)
4. phase6_1_ai_advisory_workspace.png (Integrated AI Advisory Workspace - Desktop 1280x1000)
"""
import os
import sys
import json
import time
import base64
import asyncio
import aiohttp
import subprocess

FLUTTER_WEB_URL = "http://localhost:8080"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ARTIFACTS_DIR = "/Users/siddheshbirewar/.gemini/antigravity/brain/ee291428-4c13-4698-b1ae-642f4c613070"
DOCS_SCREENSHOTS_DIR = "/Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/docs/screenshots"
FARM_ID = "94a1f16e-bf0d-4d3f-9bd3-d63a57189818"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(DOCS_SCREENSHOTS_DIR, exist_ok=True)

async def capture_all():
    port = 9251
    user_data_dir = f"/tmp/chrome_cdp_phase6_1_{port}"

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
            return True
        else:
            print(f"[WARN] Failed to capture: {filename}")
            return False

    try:
        async with aiohttp.ClientSession() as session:
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

                # 1. Farm Health Dashboard - Desktop (Live Synced)
                url = f"{FLUTTER_WEB_URL}/#/farms/{FARM_ID}/health"
                print(f"[E2E] Navigating to: {url}")
                await send_cmd(ws, 10, "Page.navigate", {"url": url})
                print("Waiting 8s for Flutter Web to load Farm Health Dashboard...")
                await asyncio.sleep(8.0)
                await save_shot(ws, 11, "phase6_1_farm_health_dashboard_desktop.png")

                # 2. Farm Health Dashboard - Offline Mode Banner
                url_offline = f"{FLUTTER_WEB_URL}/#/farms/{FARM_ID}/health?offline=true"
                print(f"[E2E] Navigating to: {url_offline}")
                await send_cmd(ws, 15, "Page.navigate", {"url": url_offline})
                print("Waiting 6s for Offline Banner Dashboard...")
                await asyncio.sleep(6.0)
                await save_shot(ws, 16, "phase6_1_offline_resilience_banner.png")

                # 3. Farm Health Dashboard - Mobile Responsive
                print("[E2E] Resizing to Mobile 390x844...")
                await send_cmd(ws, 20, "Emulation.setDeviceMetricsOverride", {
                    "width": 390,
                    "height": 844,
                    "deviceScaleFactor": 2.0,
                    "mobile": True,
                })
                # Re-navigate without offline parameter for clean mobile view
                await send_cmd(ws, 22, "Page.navigate", {"url": url})
                await asyncio.sleep(5.0)
                await save_shot(ws, 23, "phase6_1_farm_health_dashboard_mobile.png")

                # Restore Desktop
                await send_cmd(ws, 30, "Emulation.setDeviceMetricsOverride", {
                    "width": 1280,
                    "height": 1000,
                    "deviceScaleFactor": 1.0,
                    "mobile": False,
                })

                # 4. Integrated AI Advisory
                url_adv = f"{FLUTTER_WEB_URL}/#/advisory"
                print(f"[E2E] Navigating to: {url_adv}")
                await send_cmd(ws, 40, "Page.navigate", {"url": url_adv})
                print("Waiting 6s for Advisory screen...")
                await asyncio.sleep(6.0)
                await save_shot(ws, 41, "phase6_1_ai_advisory_workspace.png")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(capture_all())
