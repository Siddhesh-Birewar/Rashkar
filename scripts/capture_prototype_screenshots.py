import asyncio
import base64
import json
import os
import shutil
import subprocess
import time
import httpx
import aiohttp

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = "/Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/docs/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = [
    {
        "name": "dashboard_desktop.png",
        "url": "http://localhost:8080/#/",
        "width": 1280,
        "height": 800,
        "device_scale": 1.0,
        "mobile": False,
        "wait": 3.0,
    },
    {
        "name": "dashboard_mobile.png",
        "url": "http://localhost:8080/#/",
        "width": 375,
        "height": 667,
        "device_scale": 2.0,
        "mobile": True,
        "wait": 3.0,
    },
    {
        "name": "soil_intelligence_desktop.png",
        "url": "http://localhost:8080/#/soil-testing",
        "width": 1280,
        "height": 800,
        "device_scale": 1.0,
        "mobile": False,
        "wait": 3.5,
    },
    {
        "name": "weather_desktop.png",
        "url": "http://localhost:8080/#/weather",
        "width": 1280,
        "height": 800,
        "device_scale": 1.0,
        "mobile": False,
        "wait": 3.5,
    },
    {
        "name": "crops_catalog_desktop.png",
        "url": "http://localhost:8080/#/crop-recommendation",
        "width": 1280,
        "height": 800,
        "device_scale": 1.0,
        "mobile": False,
        "wait": 3.5,
    },
    {
        "name": "crops_catalog_mobile.png",
        "url": "http://localhost:8080/#/crop-recommendation",
        "width": 375,
        "height": 667,
        "device_scale": 2.0,
        "mobile": True,
        "wait": 3.5,
    },
    {
        "name": "advisory_desktop.png",
        "url": "http://localhost:8080/#/advisory",
        "width": 1280,
        "height": 800,
        "device_scale": 1.0,
        "mobile": False,
        "wait": 4.0,
    },
    {
        "name": "advisory_mobile.png",
        "url": "http://localhost:8080/#/advisory",
        "width": 375,
        "height": 667,
        "device_scale": 2.0,
        "mobile": True,
        "wait": 4.0,
    },
    {
        "name": "advisory_tablet.png",
        "url": "http://localhost:8080/#/advisory",
        "width": 768,
        "height": 1024,
        "device_scale": 1.5,
        "mobile": False,
        "wait": 4.0,
    },
    {
        "name": "history_desktop.png",
        "url": "http://localhost:8080/#/history",
        "width": 1280,
        "height": 800,
        "device_scale": 1.0,
        "mobile": False,
        "wait": 3.5,
    },
]

async def capture_target(ws, target):
    print(f"Navigating to {target['url']} ({target['width']}x{target['height']})...")
    
    # 1. Metrics override
    await ws.send_json({
        "id": 10,
        "method": "Emulation.setDeviceMetricsOverride",
        "params": {
            "width": target["width"],
            "height": target["height"],
            "deviceScaleFactor": target["device_scale"],
            "mobile": target["mobile"],
        }
    })
    
    # Drain messages until response id 10
    while True:
        m = await ws.receive_json()
        if m.get("id") == 10:
            break

    # 2. Navigate
    await ws.send_json({
        "id": 20,
        "method": "Page.navigate",
        "params": {"url": target["url"]}
    })
    while True:
        m = await ws.receive_json()
        if m.get("id") == 20:
            break

    # 3. Wait for Flutter Web to compile shaders, render DOM / canvas
    await asyncio.sleep(target.get("wait", 3.0))

    # 4. Capture screenshot
    await ws.send_json({
        "id": 30,
        "method": "Page.captureScreenshot",
        "params": {"format": "png"}
    })

    while True:
        m = await ws.receive_json()
        if m.get("id") == 30:
            img_b64 = m["result"]["data"]
            out_file = os.path.join(OUT_DIR, target["name"])
            with open(out_file, "wb") as f:
                f.write(base64.b64decode(img_b64))
            size = os.path.getsize(out_file)
            print(f"-> Saved {target['name']}: {size} bytes")
            break

async def main():
    profile_dir = "/tmp/cropnet-chrome-profile"
    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir, ignore_errors=True)
    os.makedirs(profile_dir, exist_ok=True)

    chrome_proc = subprocess.Popen([
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--remote-debugging-port=9222",
        f"--user-data-dir={profile_dir}",
        "--disable-background-networking",
        "--disable-default-apps",
        "--no-first-run",
        "about:blank"
    ])
    time.sleep(2.0)

    try:
        r = httpx.get("http://127.0.0.1:9222/json/list")
        tabs = r.json()
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        if not page_tabs:
            raise RuntimeError("No page target found in Chrome DevTools")
        ws_url = page_tabs[0]["webSocketDebuggerUrl"]
        print(f"Connecting to CDP: {ws_url}")

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url, max_msg_size=16*1024*1024) as ws:
                await ws.send_json({"id": 1, "method": "Page.enable"})
                while True:
                    m = await ws.receive_json()
                    if m.get("id") == 1:
                        break

                for t in TARGETS:
                    await capture_target(ws, t)

    finally:
        chrome_proc.terminate()
        chrome_proc.wait()
        shutil.rmtree(profile_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(main())
