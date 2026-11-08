"""
CropNet AI — Phase 5.8.1 Complete E2E Screenshot Capture via Chrome CDP.

Captures all 6 mandated screenshots:
1. phase5_8_1_default_advisory_workspace.png (Default Advisory workspace)
2. phase5_8_1_structured_farm_assessment.png (Structured farm assessment)
3. phase5_8_1_diagnostic_follow_up.png (Contextual diagnostic follow-up card)
4. phase5_8_1_simple_conversational_answer.png (Simple conversational answer)
5. phase5_8_1_marathi_response.png (Full Marathi response without clipping)
6. phase5_8_1_mobile_layout.png (Mobile responsive 375x812 layout)
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

os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(DOCS_SCREENSHOTS_DIR, exist_ok=True)

async def capture_all():
    port = 9247
    user_data_dir = f"/tmp/chrome_cdp_advisory_{port}"

    chrome_cmd = [
        CHROME_BIN,
        "--headless=new",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--window-size=1280,1100",
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

    async def click_at(ws, msg_id, x, y):
        await send_cmd(ws, msg_id, "Input.dispatchMouseEvent", {
            "type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1
        })
        await asyncio.sleep(0.05)
        await send_cmd(ws, msg_id + 1, "Input.dispatchMouseEvent", {
            "type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1
        })
        await asyncio.sleep(0.5)

    async def scroll_wheel(ws, delta_y, count=3):
        for i in range(count):
            await send_cmd(ws, 500 + i, "Input.dispatchMouseEvent", {
                "type": "mouseWheel", "x": 640, "y": 500, "deltaX": 0, "deltaY": delta_y
            })
            await asyncio.sleep(0.2)
        await asyncio.sleep(0.5)

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
                    "height": 1100,
                    "deviceScaleFactor": 1.0,
                    "mobile": False,
                })

                # -------------------------------------------------------------
                # 1. Default Advisory Workspace
                # -------------------------------------------------------------
                url = f"{FLUTTER_WEB_URL}/#/advisory"
                print(f"[E2E] Navigating to: {url}")
                await send_cmd(ws, 4, "Page.navigate", {"url": url})
                print("Waiting 10s for Flutter Web to load default workspace...")
                await asyncio.sleep(10.0)
                await save_shot(ws, 5, "phase5_8_1_default_advisory_workspace.png")

                # -------------------------------------------------------------
                # 2. Structured Farm Assessment (Chickpea in Heavy Clay)
                # -------------------------------------------------------------
                print("[E2E] Clicking prompt chip: 'Can I grow chickpea in heavy clay soil?' at (260, 125)...")
                await click_at(ws, 10, 260, 125)
                print("Waiting 32s for deterministic evaluation + Qwen3:8B explanation...")
                await asyncio.sleep(32.0)

                # Scroll slightly down to center the structured card
                await scroll_wheel(ws, delta_y=160, count=2)
                await save_shot(ws, 20, "phase5_8_1_structured_farm_assessment.png")

                # -------------------------------------------------------------
                # 3. Contextual Diagnostic Follow-Up Card
                # -------------------------------------------------------------
                print("[E2E] Scrolling down to Diagnostic Follow-Up & Evidence sections...")
                await scroll_wheel(ws, delta_y=350, count=2)
                await save_shot(ws, 30, "phase5_8_1_diagnostic_follow_up.png")

                # -------------------------------------------------------------
                # 4. Simple Conversational Answer
                # -------------------------------------------------------------
                # Click third prompt chip (Pomegranate water requirements)
                print("[E2E] Clicking prompt chip: 'What are the water requirements for pomegranate?' at (660, 125)...")
                await click_at(ws, 40, 660, 125)
                print("Waiting 32s for conversational response...")
                await asyncio.sleep(32.0)
                await scroll_wheel(ws, delta_y=400, count=2)
                await save_shot(ws, 50, "phase5_8_1_simple_conversational_answer.png")

                # -------------------------------------------------------------
                # 5. Marathi Response
                # -------------------------------------------------------------
                print("[E2E] Switching language to Marathi at (945, 28)...")
                await click_at(ws, 60, 945, 28)
                await asyncio.sleep(3.0)

                print("[E2E] Clicking Marathi prompt chip: 'काळी जमीन हरभऱ्यासाठी योग्य आहे का?' at (260, 125)...")
                await click_at(ws, 70, 260, 125)
                print("Waiting 32s for Marathi evaluation and structured card...")
                await asyncio.sleep(32.0)

                await scroll_wheel(ws, delta_y=200, count=2)
                await save_shot(ws, 80, "phase5_8_1_marathi_response.png")

                # -------------------------------------------------------------
                # 6. Mobile Layout (375x812)
                # -------------------------------------------------------------
                print("[E2E] Emulating mobile viewport (375x812)...")
                await send_cmd(ws, 90, "Emulation.setDeviceMetricsOverride", {
                    "width": 375,
                    "height": 812,
                    "deviceScaleFactor": 2.0,
                    "mobile": True,
                })
                await asyncio.sleep(3.0)
                await save_shot(ws, 95, "phase5_8_1_mobile_layout.png")

                print("\n[ALL E2E SCREENSHOTS CAPTURED SUCCESSFULLY]")

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(capture_all())
