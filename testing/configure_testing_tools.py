#!/usr/bin/env python3
"""
Surgical-Precision Testing - Testing Tools Configuration and Validation
This script configures and validates all required testing tools for the Future Social (FS) project.
"""

import os
import sys
import json
import subprocess
import logging
import datetime
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("testing/testing_tools_setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_testing_tools")

class TestingToolsConfiguration:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.tools_dir = self.test_env_dir / "tools"
        self.config_dir = self.test_env_dir / "configs"
        self.venv_dir = self.test_env_dir / "venv"
        self.tools_status_file = self.test_env_dir / "testing_tools_status.json"
        
        # Ensure directories exist
        self.tools_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        logger.info(f"Testing tools configuration initialized for project at {self.project_root}")

    def get_venv_python(self):
        """Get the path to the Python executable in the virtual environment"""
        if os.name == 'nt':  # Windows
            python_path = self.venv_dir / "Scripts" / "python.exe"
        else:  # Unix/Linux/Mac
            python_path = self.venv_dir / "bin" / "python"
        
        return str(python_path) if python_path.exists() else sys.executable

    def get_venv_pip(self):
        """Get the path to the pip executable in the virtual environment"""
        if os.name == 'nt':  # Windows
            pip_path = self.venv_dir / "Scripts" / "pip.exe"
        else:  # Unix/Linux/Mac
            pip_path = self.venv_dir / "bin" / "pip"
        
        return str(pip_path) if pip_path.exists() else "pip"

    def configure_pytest(self):
        """Configure pytest and related plugins"""
        logger.info("Configuring pytest and related plugins...")
        
        # Define pytest plugins to install
        pytest_plugins = [
            "pytest-cov",       # Coverage reporting
            "pytest-mock",      # Mocking support
            "pytest-flask",     # Flask testing support
            "pytest-benchmark", # Performance benchmarking
            "pytest-xdist",     # Parallel test execution
            "pytest-html",      # HTML report generation
            "pytest-timeout",   # Test timeout support
            "pytest-randomly"   # Random test ordering
        ]
        
        # Install pytest and plugins
        try:
            pip_path = self.get_venv_pip()
            cmd = [pip_path, "install", "pytest"] + pytest_plugins
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Installed pytest and plugins: {', '.join(['pytest'] + pytest_plugins)}")
            
            # Create pytest configuration file
            pytest_ini = """
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=src --cov-report=html:testing/results/coverage --html=testing/results/pytest_report.html
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    slow: Slow running tests
    security: Security tests
"""
            with open(self.project_root / "pytest.ini", 'w') as f:
                f.write(pytest_ini.strip())
            logger.info("Created pytest.ini configuration file")
            
            # Create directory for pytest results
            (self.test_results_dir / "coverage").mkdir(exist_ok=True)
            
            # Verify pytest installation
            python_path = self.get_venv_python()
            version_cmd = [python_path, "-m", "pytest", "--version"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Pytest verification: {version_result.stdout.strip()}")
            
            return {
                "status": "success",
                "version": version_result.stdout.strip(),
                "plugins": pytest_plugins,
                "config_file": str(self.project_root / "pytest.ini")
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure pytest: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return {
                "status": "error",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }

    def configure_flake8(self):
        """Configure flake8 for code linting"""
        logger.info("Configuring flake8 for code linting...")
        
        try:
            # Install flake8 and plugins
            pip_path = self.get_venv_pip()
            flake8_plugins = [
                "flake8-docstrings",  # Docstring style checking
                "flake8-import-order", # Import order checking
                "flake8-bugbear",     # Bug detection
                "flake8-bandit",      # Security issues
                "flake8-annotations"  # Type annotation checking
            ]
            cmd = [pip_path, "install", "flake8"] + flake8_plugins
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Installed flake8 and plugins: {', '.join(['flake8'] + flake8_plugins)}")
            
            # Create flake8 configuration
            flake8_config = """
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist,venv,testing/venv
select = C,E,F,W,B,B950
ignore = E203,E501,W503
per-file-ignores =
    __init__.py:F401
    tests/*:D100,D101,D102,D103
"""
            with open(self.project_root / ".flake8", 'w') as f:
                f.write(flake8_config.strip())
            logger.info("Created .flake8 configuration file")
            
            # Verify flake8 installation
            python_path = self.get_venv_python()
            version_cmd = [python_path, "-m", "flake8", "--version"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Flake8 verification: {version_result.stdout.strip()}")
            
            return {
                "status": "success",
                "version": version_result.stdout.strip(),
                "plugins": flake8_plugins,
                "config_file": str(self.project_root / ".flake8")
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure flake8: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return {
                "status": "error",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }

    def configure_security_tools(self):
        """Configure security testing tools"""
        logger.info("Configuring security testing tools...")
        
        try:
            # Install security tools
            pip_path = self.get_venv_pip()
            security_tools = [
                "bandit",       # Security linter
                "safety",       # Dependency vulnerability checking
                "python-owasp-zap-v2.4", # OWASP ZAP API (corrected package name)
                "pyjwt",        # JWT handling
                "cryptography"  # Cryptographic operations
            ]
            cmd = [pip_path, "install"] + security_tools
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Installed security tools: {', '.join(security_tools)}")
            
            # Create bandit configuration
            bandit_config = """
[bandit]
exclude_dirs = testing/venv,venv,tests
"""
            with open(self.config_dir / "bandit.conf", 'w') as f:
                f.write(bandit_config.strip())
            logger.info("Created bandit configuration file")
            
            # Verify bandit installation
            python_path = self.get_venv_python()
            version_cmd = [python_path, "-m", "bandit", "--version"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Bandit verification: {version_result.stdout.strip()}")
            
            return {
                "status": "success",
                "tools": security_tools,
                "bandit_version": version_result.stdout.strip(),
                "config_file": str(self.config_dir / "bandit.conf")
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure security tools: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return {
                "status": "error",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }

    def configure_performance_tools(self):
        """Configure performance testing tools"""
        logger.info("Configuring performance testing tools...")
        
        try:
            # Install performance tools
            pip_path = self.get_venv_pip()
            performance_tools = [
                "locust",       # Load testing
                "pyinstrument", # Profiling
                "memory_profiler", # Memory profiling
                "psutil",       # System monitoring
                "requests"      # HTTP requests
            ]
            cmd = [pip_path, "install"] + performance_tools
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Installed performance tools: {', '.join(performance_tools)}")
            
            # Create locust configuration
            locustfile_content = """
from locust import HttpUser, task, between

class FutureSocialUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def index(self):
        self.client.get("/")
    
    @task(3)
    def view_user(self):
        user_id = 1  # This would be randomized in a real test
        self.client.get(f"/users/{user_id}")
    
    @task(2)
    def view_posts(self):
        self.client.get("/posts")
"""
            with open(self.tools_dir / "locustfile.py", 'w') as f:
                f.write(locustfile_content.strip())
            logger.info("Created locustfile.py for load testing")
            
            # Verify locust installation
            python_path = self.get_venv_python()
            version_cmd = [python_path, "-m", "locust", "--version"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Locust verification: {version_result.stdout.strip()}")
            
            return {
                "status": "success",
                "tools": performance_tools,
                "locust_version": version_result.stdout.strip(),
                "locustfile": str(self.tools_dir / "locustfile.py")
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure performance tools: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return {
                "status": "error",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }

    def configure_accessibility_tools(self):
        """Configure accessibility testing tools"""
        logger.info("Configuring accessibility testing tools...")
        
        try:
            # Install accessibility tools
            pip_path = self.get_venv_pip()
            accessibility_tools = [
                "axe-selenium-python", # Accessibility testing with Selenium
                "selenium",           # Web browser automation
                "webdriver-manager"   # WebDriver management
            ]
            cmd = [pip_path, "install"] + accessibility_tools
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Installed accessibility tools: {', '.join(accessibility_tools)}")
            
            # Create accessibility test script
            accessibility_script = """
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
"""
            with open(self.tools_dir / "accessibility_test.py", 'w') as f:
                f.write(accessibility_script.strip())
            logger.info("Created accessibility_test.py script")
            
            # Create directory for accessibility results
            (self.test_results_dir / "accessibility").mkdir(exist_ok=True)
            
            # Verify selenium installation
            python_path = self.get_venv_python()
            version_cmd = [python_path, "-c", "import selenium; print(f'Selenium {selenium.__version__}')"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Selenium verification: {version_result.stdout.strip()}")
            
            return {
                "status": "success",
                "tools": accessibility_tools,
                "selenium_version": version_result.stdout.strip(),
                "test_script": str(self.tools_dir / "accessibility_test.py")
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure accessibility tools: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return {
                "status": "error",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }
        except Exception as e:
            logger.error(f"Failed to configure accessibility tools: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def configure_visual_regression_tools(self):
        """Configure visual regression testing tools"""
        logger.info("Configuring visual regression testing tools...")
        
        try:
            # Install visual regression tools
            pip_path = self.get_venv_pip()
            visual_tools = [
                "selenium",           # Web browser automation
                "webdriver-manager",  # WebDriver management
                "Pillow",             # Image processing
                "opencv-python",      # Computer vision
                "scikit-image"        # Image processing
            ]
            cmd = [pip_path, "install"] + visual_tools
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Installed visual regression tools: {', '.join(visual_tools)}")
            
            # Create visual regression test script
            visual_script = """
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
"""
            with open(self.tools_dir / "visual_regression_test.py", 'w') as f:
                f.write(visual_script.strip())
            logger.info("Created visual_regression_test.py script")
            
            # Create directories for visual regression results
            (self.test_results_dir / "visual_regression").mkdir(exist_ok=True)
            (self.test_results_dir / "visual_regression" / "baseline").mkdir(exist_ok=True)
            (self.test_results_dir / "visual_regression" / "current").mkdir(exist_ok=True)
            (self.test_results_dir / "visual_regression" / "diff").mkdir(exist_ok=True)
            
            # Verify PIL installation
            python_path = self.get_venv_python()
            version_cmd = [python_path, "-c", "from PIL import Image; import PIL; print(f'Pillow {PIL.__version__}')"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Pillow verification: {version_result.stdout.strip()}")
            
            return {
                "status": "success",
                "tools": visual_tools,
                "pillow_version": version_result.stdout.strip(),
                "test_script": str(self.tools_dir / "visual_regression_test.py")
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure visual regression tools: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return {
                "status": "error",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }
        except Exception as e:
            logger.error(f"Failed to configure visual regression tools: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def configure_api_testing_tools(self):
        """Configure API testing tools"""
        logger.info("Configuring API testing tools...")
        
        try:
            # Install API testing tools
            pip_path = self.get_venv_pip()
            api_tools = [
                "requests",      # HTTP requests
                "pytest-mock",   # Mocking
                "responses",     # HTTP response mocking
                "jsonschema",    # JSON schema validation
                "tavern"         # API testing
            ]
            cmd = [pip_path, "install"] + api_tools
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Installed API testing tools: {', '.join(api_tools)}")
            
            # Create API test script
            api_test_script = """
import requests
import json
import os
from pathlib import Path
import jsonschema
import datetime

class ApiTester:
    def __init__(self):
        self.test_results_dir = Path(__file__).parent.parent / "results" / "api_tests"
        self.test_results_dir.mkdir(exist_ok=True)
        self.schemas_dir = Path(__file__).parent.parent / "schemas"
        self.schemas_dir.mkdir(exist_ok=True)
        
        # Create basic schemas if they don't exist
        self._create_default_schemas()
    
    def _create_default_schemas(self):
        # Create default JSON schemas for API validation
        user_schema = {
            "type": "object",
            "required": ["id", "username", "email"],
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            }
        }
        
        post_schema = {
            "type": "object",
            "required": ["id", "title", "content", "user_id"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "user_id": {"type": "integer"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        }
        
        # Save schemas
        with open(self.schemas_dir / "user_schema.json", 'w') as f:
            json.dump(user_schema, f, indent=2)
        
        with open(self.schemas_dir / "post_schema.json", 'w') as f:
            json.dump(post_schema, f, indent=2)
    
    def test_endpoint(self, url, method="GET", data=None, headers=None, expected_status=200, schema=None):
        # Test an API endpoint
        result = {
            "url": url,
            "method": method,
            "timestamp": datetime.datetime.now().isoformat(),
            "expected_status": expected_status,
            "data_sent": data,
            "headers_sent": headers
        }
        
        try:
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                params=data if method == "GET" else None,
                headers=headers or {}
            )
            
            # Record response details
            result["status_code"] = response.status_code
            result["response_time_ms"] = response.elapsed.total_seconds() * 1000
            result["headers_received"] = dict(response.headers)
            
            try:
                result["response_body"] = response.json()
            except:
                result["response_body"] = response.text
            
            # Check status code
            result["status_match"] = response.status_code == expected_status
            
            # Validate schema if provided
            if schema and isinstance(result["response_body"], (dict, list)):
                try:
                    if isinstance(schema, str) and os.path.exists(schema):
                        with open(schema, 'r') as f:
                            schema_data = json.load(f)
                    else:
                        schema_data = schema
                    
                    jsonschema.validate(result["response_body"], schema_data)
                    result["schema_valid"] = True
                except jsonschema.exceptions.ValidationError as e:
                    result["schema_valid"] = False
                    result["schema_error"] = str(e)
            
            # Overall test result
            result["success"] = result.get("status_match", False) and result.get("schema_valid", True)
            
        except requests.exceptions.RequestException as e:
            result["error"] = str(e)
            result["success"] = False
        
        # Save result
        endpoint_name = url.split("/")[-1] or "root"
        result_file = self.test_results_dir / f"{method}_{endpoint_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def run_test_suite(self, base_url, endpoints):
        # Run a suite of API tests
        results = []
        for endpoint in endpoints:
            url = f"{base_url}{endpoint['path']}"
            result = self.test_endpoint(
                url=url,
                method=endpoint.get("method", "GET"),
                data=endpoint.get("data"),
                headers=endpoint.get("headers"),
                expected_status=endpoint.get("expected_status", 200),
                schema=endpoint.get("schema")
            )
            results.append(result)
        
        # Save summary
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "base_url": base_url,
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r.get("success", False)),
            "failed_tests": sum(1 for r in results if not r.get("success", False)),
            "results": results
        }
        
        summary_file = self.test_results_dir / f"test_suite_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

if __name__ == "__main__":
    # Example usage
    tester = ApiTester()
    
    # Define test endpoints
    endpoints = [
        {"path": "/users", "method": "GET", "expected_status": 200},
        {"path": "/users/1", "method": "GET", "expected_status": 200, "schema": "schemas/user_schema.json"},
        {"path": "/posts", "method": "GET", "expected_status": 200}
    ]
    
    # Run tests
    results = tester.run_test_suite("http://localhost:5000", endpoints)
    print(f"Tests completed: {results['successful_tests']}/{results['total_tests']} successful")
"""
            with open(self.tools_dir / "api_tester.py", 'w') as f:
                f.write(api_test_script.strip())
            logger.info("Created api_tester.py script")
            
            # Create directories for API test results
            (self.test_results_dir / "api_tests").mkdir(exist_ok=True)
            (self.test_env_dir / "schemas").mkdir(exist_ok=True)
            
            # Verify requests installation
            python_path = self.get_venv_python()
            version_cmd = [python_path, "-c", "import requests; print(f'Requests {requests.__version__}')"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Requests verification: {version_result.stdout.strip()}")
            
            return {
                "status": "success",
                "tools": api_tools,
                "requests_version": version_result.stdout.strip(),
                "test_script": str(self.tools_dir / "api_tester.py")
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure API testing tools: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return {
                "status": "error",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }
        except Exception as e:
            logger.error(f"Failed to configure API testing tools: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def run_setup(self):
        """Run the complete setup process"""
        logger.info("Starting testing tools configuration...")
        
        try:
            # Configure all testing tools
            results = {
                "timestamp": datetime.datetime.now().isoformat(),
                "pytest": self.configure_pytest(),
                "flake8": self.configure_flake8(),
                "security_tools": self.configure_security_tools(),
                "performance_tools": self.configure_performance_tools(),
                "accessibility_tools": self.configure_accessibility_tools(),
                "visual_regression_tools": self.configure_visual_regression_tools(),
                "api_testing_tools": self.configure_api_testing_tools()
            }
            
            # Determine overall status
            success_count = sum(1 for tool, result in results.items() 
                              if tool != "timestamp" and result.get("status") == "success")
            total_tools = len(results) - 1  # Exclude timestamp
            
            results["overall_status"] = "success" if success_count == total_tools else "partial"
            results["success_rate"] = f"{success_count}/{total_tools}"
            
            # Save results
            with open(self.tools_status_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Create a human-readable summary
            summary_file = self.test_env_dir / "testing_tools_summary.md"
            with open(summary_file, 'w') as f:
                f.write("# Testing Tools Configuration Summary\n\n")
                f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")
                f.write(f"Overall Status: **{results['overall_status']}** ({results['success_rate']} tools configured successfully)\n\n")
                
                for tool, result in results.items():
                    if tool == "timestamp":
                        continue
                    
                    f.write(f"## {tool.replace('_', ' ').title()}\n\n")
                    status = result.get('status', 'unknown') if isinstance(result, dict) else 'unknown'
                    f.write(f"Status: **{status}**\n\n")
                    
                    if isinstance(result, dict) and result.get("status") == "success":
                        if "version" in result:
                            f.write(f"Version: {result['version']}\n\n")
                        
                        if "tools" in result:
                            f.write("Installed tools:\n")
                            for tool_name in result["tools"]:
                                f.write(f"- {tool_name}\n")
                            f.write("\n")
                        
                        if "plugins" in result:
                            f.write("Installed plugins:\n")
                            for plugin in result["plugins"]:
                                f.write(f"- {plugin}\n")
                            f.write("\n")
                        
                        if "config_file" in result:
                            f.write(f"Configuration file: `{result['config_file']}`\n\n")
                        
                        if "test_script" in result:
                            f.write(f"Test script: `{result['test_script']}`\n\n")
                    else:
                        if "error" in result:
                            f.write(f"Error: {result['error']}\n\n")
            
            logger.info(f"Testing tools configuration completed with status: {results['overall_status']}")
            logger.info(f"Summary saved to {summary_file}")
            
            return results
            
        except Exception as e:
            logger.error(f"Testing tools configuration failed: {e}")
            raise

if __name__ == "__main__":
    setup = TestingToolsConfiguration()
    setup.run_setup()
