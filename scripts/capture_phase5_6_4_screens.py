import asyncio
import base64
import json
import os
import subprocess
import time
import aiohttp

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = "/Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/docs/screenshots"
ARTIFACT_DIR = "/Users/siddheshbirewar/.gemini/antigravity/brain/ee291428-4c13-4698-b1ae-642f4c613070"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

FARM_ID = "6de1e672-5044-41cb-be9f-b23678906453"
REPORT_ID = "260307c1-a0e3-469c-b8fb-c4a9b8895853"

TARGETS = [
    {
        "name": "phase5_6_4_soil_intelligence_overview.png",
        "url": f"http://localhost:8080/#/soil-testing/{FARM_ID}",
        "width": 1280,
        "height": 900,
        "wait": 4.5,
    },
    {
        "name": "phase5_6_4_soil_report_history.png",
        "url": f"http://localhost:8080/#/soil-testing/{FARM_ID}/lab/history",
        "width": 1280,
        "height": 900,
        "wait": 4.5,
    },
    {
        "name": "phase5_6_4_soil_report_review.png",
        "url": f"http://localhost:8080/#/soil-testing/{FARM_ID}/lab/reports/{REPORT_ID}",
        "width": 1280,
        "height": 900,
        "wait": 4.5,
    },
]

async def capture():
    # Launch Chrome headless with remote debugging
    proc = subprocess.Popen([
        CHROME_BIN,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-extensions",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(1.5)

    try:
        async with aiohttp.ClientSession() as session:
            # Get list of targets
            async with session.get("http://127.0.0.1:9222/json") as resp:
                targets_data = await resp.json()
                ws_url = targets_data[0]["webSocketDebuggerUrl"]

            async with session.ws_connect(ws_url) as ws:
                msg_id = 1
                for t in TARGETS:
                    print(f"Capturing {t['name']} from {t['url']}...")
                    # Set viewport
                    msg_id += 1
                    await ws.send_json({
                        "id": msg_id,
                        "method": "Emulation.setDeviceMetricsOverride",
                        "params": {
                            "width": t["width"],
                            "height": t["height"],
                            "deviceScaleFactor": 1.0,
                            "mobile": False,
                        }
                    })
                    await ws.receive_json()

                    # Navigate
                    msg_id += 1
                    await ws.send_json({
                        "id": msg_id,
                        "method": "Page.navigate",
                        "params": {"url": t["url"]}
                    })
                    await ws.receive_json()

                    await asyncio.sleep(t["wait"])

                    # Take screenshot
                    msg_id += 1
                    await ws.send_json({
                        "id": msg_id,
                        "method": "Page.captureScreenshot",
                        "params": {"format": "png"}
                    })
                    resp_data = await ws.receive_json()
                    img_data = base64.b64decode(resp_data["result"]["data"])

                    out_path = os.path.join(OUT_DIR, t["name"])
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"[OK] Saved to {out_path} ({len(img_data)} bytes)")

                    art_path = os.path.join(ARTIFACT_DIR, t["name"])
                    with open(art_path, "wb") as f:
                        f.write(img_data)
                    print(f"[OK] Copied to artifact {art_path}")

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(capture())
