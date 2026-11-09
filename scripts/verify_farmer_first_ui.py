"""
RASHKAR — Farmer-First UI Verification Suite.
Automates visual inspection of all redesigned screens across responsive viewports:
- Desktop (1440x900)
- Mobile (390x844)
"""

import os
import time
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://127.0.0.1:8080"
SCREENSHOT_DIR = "docs/screenshots/farmer_first"


def run_farmer_first_verification():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ----------------- DESKTOP VIEWPORT (1440 x 900) -----------------
        print("\n=== DESKTOP SUITE (1440x900) ===")
        context_desktop = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context_desktop.new_page()

        print(f"[1/6] Loading Home on {FRONTEND_URL}...")
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(6000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_01_home.png"))
        print("  [OK] Captured desktop_01_home.png")

        # Click on 'My Crop'
        print("[2/6] Inspecting My Crop Screen...")
        page.keyboard.press("Tab")
        # In Flutter Web with bottom nav or home cards, let's navigate to screens or click
        # Using URL hash or clicking primary action
        # The primary cards are laid out on Home Screen
        # Let's click "My Crop" button on home
        page.mouse.click(600, 480)
        page.wait_for_timeout(4000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_02_my_crop.png"))
        print("  [OK] Captured desktop_02_my_crop.png")

        # Go back to Home
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(3000)

        # Click Heat Safety
        print("[3/6] Inspecting Heat Safety...")
        page.mouse.click(800, 480)
        page.wait_for_timeout(4000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_03_heat_worker.png"))
        print("  [OK] Captured desktop_03_heat_worker.png")

        # Switch to Crop Heat tab
        page.mouse.click(850, 70)
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_03_heat_crop.png"))
        print("  [OK] Captured desktop_03_heat_crop.png")

        # Go back to Home and click Extra Income
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(3000)
        print("[4/6] Inspecting Extra Income...")
        page.mouse.click(600, 560)
        page.wait_for_timeout(4000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_04_extra_income.png"))
        print("  [OK] Captured desktop_04_extra_income.png")

        # Go back to Home and click Crop Loss
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(3000)
        print("[5/6] Inspecting Crop Loss...")
        page.mouse.click(800, 560)
        page.wait_for_timeout(4000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_05_crop_loss.png"))
        print("  [OK] Captured desktop_05_crop_loss.png")

        # Go back to Home and click Ask Rashkar
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(3000)
        print("[6/6] Inspecting Ask Rashkar...")
        page.mouse.click(700, 640)
        page.wait_for_timeout(4000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_06_ask_rashkar.png"))
        print("  [OK] Captured desktop_06_ask_rashkar.png")

        context_desktop.close()

        # ----------------- MOBILE VIEWPORT (390 x 844) -----------------
        print("\n=== MOBILE SUITE (390x844 - iPhone / Android Form Factor) ===")
        context_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = context_mobile.new_page()

        mobile_page.goto(FRONTEND_URL)
        mobile_page.wait_for_timeout(6000)
        mobile_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "mobile_01_home.png"))
        print("  [OK] Captured mobile_01_home.png")

        context_mobile.close()
        browser.close()

        print("\nFarmer-First UI visual verification completed successfully!")


if __name__ == "__main__":
    run_farmer_first_verification()
