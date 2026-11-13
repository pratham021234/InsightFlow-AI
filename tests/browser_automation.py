import os
import time
import sys
from playwright.sync_api import sync_playwright

CHROME_PATH = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
BASE_URL = "http://localhost:8501"
SCREENSHOTS_DIR = os.path.abspath("assets/screenshots")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def nav_to_slug(page, slug):
    print(f"Navigating to sidebar slug: '{slug}'...")
    # Find link with href matching slug
    link = page.locator(f"a[href*='{slug}']").first
    if link.count() > 0:
        link.click()
    else:
        link_t = page.locator(f"a:has-text('{slug.replace('_', ' ')}')").first
        if link_t.count() > 0:
            link_t.click()
        else:
            page.goto(f"{BASE_URL}/{slug}")
    time.sleep(3)

def run_browser_tests():
    print(f"Launching Chrome from: {CHROME_PATH}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        results = {}

        try:
            # Scenario A: Initial Application
            print("\n[1/11] Running Scenario A: Initial Application Landing...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_selector("h1:has-text('InsightFlow AI')", timeout=15000)
            results["Scenario A (Landing Page)"] = "PASSED"
            print(" Scenario A passed.")

            # Scenario B: Dataset Ingestion via Sample Dataset
            print("\n[2/11] Running Scenario B: Loading Sample Dataset...")
            sample_btn = page.locator("button:has-text('Load Sample Sales Dataset')")
            sample_btn.click()
            page.wait_for_selector("text=Active Dataset:", timeout=15000)
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_dataset_upload.png"), full_page=False)
            results["Scenario B (Dataset Upload & Overview)"] = "PASSED"
            print(" Scenario B passed. Saved 01_dataset_upload.png")

            # Scenario C: Dataset Intelligence
            print("\n[3/11] Running Scenario C: Testing Dataset Intelligence...")
            nav_to_slug(page, "dataset_detection")
            page.wait_for_selector("h1:has-text('Dataset Intelligence')", timeout=15000)
            time.sleep(2)
            assert "Sales" in page.content()
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_dataset_intelligence.png"), full_page=False)
            results["Scenario C (Dataset Intelligence)"] = "PASSED"
            print(" Scenario C passed. Saved 02_dataset_intelligence.png")

            # Scenario D: Data Profiling Engine
            print("\n[4/11] Running Scenario D: Testing Data Profiling...")
            nav_to_slug(page, "profiling")
            page.wait_for_selector("h1:has-text('Data Profiling Engine')", timeout=15000)
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_data_profiling.png"), full_page=False)
            results["Scenario D (Data Profiling)"] = "PASSED"
            print(" Scenario D passed. Saved 03_data_profiling.png")

            # Scenario E: Interactive Data Cleaning
            print("\n[5/11] Running Scenario E: Testing Data Cleaning...")
            nav_to_slug(page, "cleaning")
            page.wait_for_selector("h1:has-text('Interactive Data Cleaning Engine')", timeout=15000)
            time.sleep(2)
            
            # Click deduplicate if present
            dedup_btn = page.locator("button:has-text('Remove Duplicate Rows')")
            if dedup_btn.count() > 0:
                dedup_btn.click()
                time.sleep(2)
                
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_data_cleaning.png"), full_page=False)
            results["Scenario E (Data Cleaning & Remediation)"] = "PASSED"
            print(" Scenario E passed. Saved 04_data_cleaning.png")

            # Scenario F: Dynamic KPI Engine
            print("\n[6/11] Running Scenario F: Testing Dynamic KPI Engine...")
            nav_to_slug(page, "kpi_dashboard")
            page.wait_for_selector("h1:has-text('Dynamic KPI Engine')", timeout=15000)
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_kpi_dashboard.png"), full_page=False)
            results["Scenario F (KPI Engine)"] = "PASSED"
            print(" Scenario F passed. Saved 05_kpi_dashboard.png")

            # Scenario G: Visual Analytics Engine
            print("\n[7/11] Running Scenario G: Testing Visual Analytics...")
            nav_to_slug(page, "visualizations")
            page.wait_for_selector("h1:has-text('Visual Analytics Engine')", timeout=15000)
            time.sleep(3)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_visual_analytics.png"), full_page=False)
            results["Scenario G (Visual Analytics)"] = "PASSED"
            print(" Scenario G passed. Saved 06_visual_analytics.png")

            # Scenario H: Strategic AI Business Insights
            print("\n[8/11] Running Scenario H: Testing Strategic AI Business Insights...")
            nav_to_slug(page, "ai_insights")
            page.wait_for_selector("h1:has-text('AI Business Insights Engine')", timeout=15000)
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_ai_insights.png"), full_page=False)
            results["Scenario H (Strategic AI Insights)"] = "PASSED"
            print(" Scenario H passed. Saved 07_ai_insights.png")

            # Scenario I: Conversational Chat With Data
            print("\n[9/11] Running Scenario I: Testing Chat With Data...")
            nav_to_slug(page, "chat_with_data")
            page.wait_for_selector("h1:has-text('Chat With Data')", timeout=15000)
            time.sleep(2)
            
            # Click first suggested query button
            first_sugg = page.locator("button:has-text('Which product generates highest revenue?')")
            if first_sugg.count() > 0:
                first_sugg.click()
                time.sleep(3)
                
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_chat_with_data.png"), full_page=False)
            results["Scenario I (Conversational Chat Engine)"] = "PASSED"
            print(" Scenario I passed. Saved 08_chat_with_data.png")

            # Scenario J: Multi-Format Report Exporter
            print("\n[10/11] Running Scenario J: Testing Report Exporter...")
            nav_to_slug(page, "reports")
            page.wait_for_selector("h1:has-text('Analytics Report Export System')", timeout=15000)
            
            compile_btn = page.locator("button:has-text('Compile Report Draft')")
            compile_btn.click()
            page.wait_for_selector("text=Document Draft Ready:", timeout=15000)
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_report_exporter.png"), full_page=False)
            results["Scenario J (Report Compilation & Export)"] = "PASSED"
            print(" Scenario J passed. Saved 09_report_exporter.png")

            # Scenario K: Responsive Viewport Check
            print("\n[11/11] Running Scenario K: Testing Responsive Viewport...")
            page.set_viewport_size({"width": 375, "height": 667})
            time.sleep(1)
            assert page.is_visible("h1")
            results["Scenario K (Responsive Mobile Viewport)"] = "PASSED"
            print(" Scenario K passed.")

        except Exception as e:
            print(f"FAILED with error: {str(e)}")
            results["ERROR"] = str(e)
            raise e
        finally:
            browser.close()

        print("\n=======================================================")
        print("    ALL 11 BROWSER TEST SCENARIOS PASSED (100%)       ")
        print("=======================================================")
        for sc, st in results.items():
            print(f"[{st}] {sc}")
        return results

if __name__ == "__main__":
    run_browser_tests()
