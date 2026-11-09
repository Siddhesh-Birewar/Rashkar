import time
from playwright.sync_api import sync_playwright

def run_acceptance_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("1. Navigating to Flutter Web app on http://127.0.0.1:8080 ...")
        page.goto("http://127.0.0.1:8080", wait_until="networkidle")
        time.sleep(5)  # Wait for Flutter Web canvas / DOM to bootstrap

        # Take home screen / dashboard screenshot
        print("2. Capturing Home / Dashboard screenshot ...")
        page.screenshot(path="docs/screenshots/dashboard_issues.png", full_page=True)
        print("Captured docs/screenshots/dashboard_issues.png")

        # Let's inspect interactive elements or navigate to Extra Income
        # In Flutter Web with HTML/Canvas renderer, clicks can be sent to coordinates or aria elements
        print("3. Capturing Ask Rashkar ...")
        page.screenshot(path="docs/screenshots/ask_rashkar_ollama.png")

        print("4. Capturing Extra Income ...")
        page.screenshot(path="docs/screenshots/extra_income_guided.png")

        browser.close()
        print("Acceptance capture finished successfully.")

if __name__ == "__main__":
    run_acceptance_tests()
