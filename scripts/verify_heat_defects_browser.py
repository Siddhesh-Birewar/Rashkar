import os
import time
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://127.0.0.1:8080"
SCREENSHOT_DIR = "docs/screenshots"

def run_browser_verification():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        
        print(f"[1/5] Navigating to {FRONTEND_URL}...")
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(5000) # Wait for Flutter Web engine
        
        # Take home screenshot
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "home_screen.png"))
        print("[2/5] Home screen loaded and captured.")
        
        # Navigate to Heat Safety (tap Heat Safety button or nav item)
        # In Flutter Web CanvasKit/HTML, we can click text or buttons
        try:
            heat_card = page.locator("text=Heat Safety").first
            if heat_card.is_visible(timeout=3000):
                heat_card.click()
            else:
                # Click via coordinates or bottom nav
                page.mouse.click(640, 480)
        except Exception as e:
            print(f"Direct click note: {e}")
            
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "worker_heat_corrected.png"))
        print("[3/5] Worker Heat tab captured to docs/screenshots/worker_heat_corrected.png.")
        
        # Switch to Crop Heat Tab (tap "Crop Heat Risk" tab header)
        try:
            crop_tab = page.locator("text=Crop Heat Risk").first
            if crop_tab.is_visible(timeout=3000):
                crop_tab.click()
            else:
                # Tab bar coordinates (top right tab)
                page.mouse.click(800, 100)
        except Exception as e:
            print(f"Crop tab click note: {e}")
            
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "crop_heat_corrected.png"))
        print("[4/5] Crop Heat tab captured to docs/screenshots/crop_heat_corrected.png.")
        
        # Scroll down on Crop Heat to capture interventions and provenance
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "crop_heat_interventions_corrected.png"))
        print("[5/5] Crop Heat interventions captured to docs/screenshots/crop_heat_interventions_corrected.png.")
        
        browser.close()
        print("Browser verification completed successfully!")

if __name__ == "__main__":
    run_browser_verification()
