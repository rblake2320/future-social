from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from axe_selenium_python import Axe
import json
import os
from pathlib import Path

def run_accessibility_test(url):
    # Setup output directory
    test_results_dir = Path(__file__).parent.parent / "results" / "accessibility"
    test_results_dir.mkdir(exist_ok=True)
    
    # Setup WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # Navigate to the page
        driver.get(url)
        
        # Initialize axe
        axe = Axe(driver)
        
        # Inject axe-core javascript into page
        axe.inject()
        
        # Run axe accessibility analysis
        results = axe.run()
        
        # Write results to file
        filename = f"accessibility_{url.replace('://', '_').replace('/', '_')}.json"
        with open(test_results_dir / filename, 'w') as f:
            f.write(json.dumps(results, indent=2))
        
        # Generate report
        violations = results["violations"]
        report = {
            "url": url,
            "timestamp": axe.get_timestamp(),
            "violations_count": len(violations),
            "violations": violations
        }
        
        report_file = test_results_dir / f"report_{url.replace('://', '_').replace('/', '_')}.json"
        with open(report_file, 'w') as f:
            f.write(json.dumps(report, indent=2))
        
        print(f"Accessibility test completed for {url}")
        print(f"Found {len(violations)} violations")
        
        return report
    finally:
        driver.quit()

if __name__ == "__main__":
    # Example usage
    run_accessibility_test("http://localhost:5000")