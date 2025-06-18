from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import cv2
import numpy as np
import os
from pathlib import Path
import time
import json

class VisualRegressionTest:
    def __init__(self):
        self.test_results_dir = Path(__file__).parent.parent / "results" / "visual_regression"
        self.test_results_dir.mkdir(exist_ok=True)
        self.baseline_dir = self.test_results_dir / "baseline"
        self.baseline_dir.mkdir(exist_ok=True)
        self.current_dir = self.test_results_dir / "current"
        self.current_dir.mkdir(exist_ok=True)
        self.diff_dir = self.test_results_dir / "diff"
        self.diff_dir.mkdir(exist_ok=True)
        
        # Setup WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1280,1024')
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def capture_screenshot(self, url, name):
        # Capture a screenshot of the given URL
        self.driver.get(url)
        time.sleep(2)  # Wait for page to load
        
        screenshot_path = self.current_dir / f"{name}.png"
        self.driver.save_screenshot(str(screenshot_path))
        return screenshot_path
    
    def compare_with_baseline(self, name):
        # Compare current screenshot with baseline
        current_img_path = self.current_dir / f"{name}.png"
        baseline_img_path = self.baseline_dir / f"{name}.png"
        diff_img_path = self.diff_dir / f"{name}.png"
        
        # If baseline doesn't exist, create it
        if not baseline_img_path.exists():
            if current_img_path.exists():
                import shutil
                shutil.copy(current_img_path, baseline_img_path)
                return {
                    "status": "baseline_created",
                    "message": f"Baseline created for {name}",
                    "baseline_path": str(baseline_img_path)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Current screenshot for {name} not found"
                }
        
        # Compare images
        current_img = cv2.imread(str(current_img_path))
        baseline_img = cv2.imread(str(baseline_img_path))
        
        # Check if images are the same size
        if current_img.shape != baseline_img.shape:
            # Resize current to match baseline
            current_img = cv2.resize(current_img, (baseline_img.shape[1], baseline_img.shape[0]))
        
        # Calculate difference
        diff = cv2.absdiff(current_img, baseline_img)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, diff_binary = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
        
        # Calculate difference percentage
        diff_percentage = (np.count_nonzero(diff_binary) / diff_binary.size) * 100
        
        # Save diff image
        cv2.imwrite(str(diff_img_path), diff)
        
        return {
            "status": "compared",
            "difference_percentage": diff_percentage,
            "current_path": str(current_img_path),
            "baseline_path": str(baseline_img_path),
            "diff_path": str(diff_img_path),
            "is_different": diff_percentage > 0.5  # Threshold for considering images different
        }
    
    def run_test(self, url, name):
        # Run visual regression test for a URL
        screenshot_path = self.capture_screenshot(url, name)
        result = self.compare_with_baseline(name)
        
        # Save result
        result_path = self.test_results_dir / f"{name}_result.json"
        with open(result_path, 'w') as f:
            json.dump({
                "url": url,
                "name": name,
                "timestamp": time.time(),
                "result": result
            }, f, indent=2)
        
        return result

if __name__ == "__main__":
    # Example usage
    test = VisualRegressionTest()
    result = test.run_test("http://localhost:5000", "homepage")
    print(result)