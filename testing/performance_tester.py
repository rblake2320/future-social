#!/usr/bin/env python3
"""
Surgical-Precision Testing - Performance and Stress Testing
This script executes performance and stress tests for the Future Social (FS) project.
"""

import os
import sys
import json
import logging
import datetime
import requests
import random
import time
from pathlib import Path
import concurrent.futures
import uuid
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("testing/performance_testing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_performance_testing")

class PerformanceTester:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.journey_dir = self.test_results_dir / "user_journeys"
        self.mapping_dir = self.test_results_dir / "element_mapping"
        self.performance_dir = self.test_results_dir / "performance_tests"
        self.performance_summary_file = self.performance_dir / "performance_test_summary.json"
        
        # Ensure directories exist
        self.performance_dir.mkdir(exist_ok=True, parents=True)
        
        # Load API routes and scenarios
        self.routes = self._load_json(self.mapping_dir / "api_routes.json")
        self.scenarios = self._load_json(self.journey_dir / "test_scenarios.json")
        
        # Base URL for API tests
        self.base_url = "http://localhost:5000"  # Default for local testing
        self.mock_mode = not self._check_services_running()

        self.session_data = {
            "auth_token": None, # Will be populated after login
            "user_id": None
        }
        
        logger.info(f"Performance tester initialized. Mock mode: {self.mock_mode}")

    def _load_json(self, file_path):
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"File not found: {file_path}")
                return []
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []

    def _check_services_running(self):
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _api_request(self, method, path, data=None, headers=None):
        url = f"{self.base_url}{path}"
        effective_headers = headers or {}
        if self.session_data.get("auth_token"):
            effective_headers["Authorization"] = f"Bearer {self.session_data['auth_token']}"

        start_time = time.perf_counter()
        try:
            if self.mock_mode:
                time.sleep(random.uniform(0.01, 0.05)) # Simulate network latency
                status_code = 200
                if "error" in path.lower(): status_code = 400 # Simple mock error
                response_json = {"mock_response": True, "path": path, "method": method}
                if method == "POST" and "login" in path:
                    response_json["token"] = "mock_token_" + str(uuid.uuid4())[:8]
                    response_json["user_id"] = 1
                elif method == "POST" and "register" in path:
                     response_json["user_id"] = 1
                
            else:
                if method.upper() == "GET":
                    response = requests.get(url, params=data, headers=effective_headers, timeout=10)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, headers=effective_headers, timeout=10)
                elif method.upper() == "PUT":
                    response = requests.put(url, json=data, headers=effective_headers, timeout=10)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=effective_headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                status_code = response.status_code
                try:
                    response_json = response.json()
                except json.JSONDecodeError:
                    response_json = {"error": "Non-JSON response", "text": response.text[:100]}
            
            latency = (time.perf_counter() - start_time) * 1000 # ms
            return {"status_code": status_code, "latency_ms": latency, "response_json": response_json, "error": None}
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000 # ms
            logger.error(f"API request failed: {method} {path} - {e}")
            return {"status_code": 0, "latency_ms": latency, "response_json": None, "error": str(e)}

    def _login_test_user(self):
        # In a real scenario, you would use a pre-defined test user or register one.
        # For simplicity, we'll mock this or use a fixed credential if not in mock_mode.
        if self.mock_mode:
            self.session_data["auth_token"] = "mock_token_perf_test"
            self.session_data["user_id"] = 1
            logger.info("Mock login successful for performance testing.")
            return True

        login_payload = {"email": "test1@example.com", "password": "TestPassword1!"}
        # First, try to register the user in case they don't exist
        self._api_request("POST", "/users/register", data=login_payload)
        
        result = self._api_request("POST", "/users/login", data=login_payload)
        if result["status_code"] == 200 and result["response_json"].get("token"):
            self.session_data["auth_token"] = result["response_json"]["token"]
            self.session_data["user_id"] = result["response_json"].get("user_id",1)
            logger.info(f"Login successful for performance testing. User ID: {self.session_data['user_id']}")
            return True
        else:
            logger.error(f"Login failed for performance testing: {result}")
            return False

    def _perform_load_test_on_endpoint(self, endpoint_info, num_users, duration_seconds):
        logger.info(f"Testing endpoint: {endpoint_info['method']} {endpoint_info['path']} with {num_users} users for {duration_seconds}s")
        results = []
        start_test_time = time.time()

        def task():
            # Construct payload if needed, simplified for this example
            payload = None
            if endpoint_info["method"] in ["POST", "PUT"]:
                # Generic payload, specific tests might need more tailored data
                payload = {"test_data": "some_value_" + str(uuid.uuid4())[:8]}
                if "post" in endpoint_info["path"] and "user_id" not in payload:
                    payload["user_id"] = self.session_data.get("user_id", 1)
                    payload["title"] = "Perf Test Post"
                    payload["content"] = "This is a performance test post."
            
            # For paths requiring an ID, try to use a common one or a random one for stress
            path = endpoint_info["path"]
            if "<int:user_id>" in path:
                path = path.replace("<int:user_id>", str(self.session_data.get("user_id", 1)))
            if "<int:post_id>" in path:
                path = path.replace("<int:post_id>", "1") # Assuming post 1 exists or mock handles it
            if "<int:conversation_id>" in path:
                path = path.replace("<int:conversation_id>", "1")
            if "<int:group_id>" in path:
                path = path.replace("<int:group_id>", "1")
            if "<int:module_id>" in path:
                path = path.replace("<int:module_id>", "1")

            return self._api_request(endpoint_info["method"], path, data=payload)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []
            while time.time() - start_test_time < duration_seconds:
                futures.append(executor.submit(task))
                time.sleep(1 / (num_users * 2)) # Basic rate limiting to spread requests
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Task execution error: {e}")
                    results.append({"status_code": 0, "latency_ms": 0, "error": str(e)})
        
        latencies = [r["latency_ms"] for r in results if r["error"] is None and r["latency_ms"] is not None]
        successful_requests = sum(1 for r in results if r["status_code"] >= 200 and r["status_code"] < 300)
        failed_requests = len(results) - successful_requests
        
        return {
            "endpoint": f"{endpoint_info['method']} {endpoint_info['path']}",
            "num_users": num_users,
            "duration_seconds": duration_seconds,
            "total_requests": len(results),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "p95_latency_ms": statistics.quantiles(latencies, n=100)[94] if latencies and len(latencies) > 1 else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "rps": successful_requests / duration_seconds if duration_seconds > 0 else 0
        }

    def run_performance_tests(self):
        logger.info("Starting performance and stress tests...")
        if not self._login_test_user() and not self.mock_mode:
            logger.error("Cannot proceed with performance tests without login.")
            return {"error": "Login failed, cannot run performance tests."}

        key_endpoints = [
            # User Service
            {"method": "POST", "path": "/users/register", "service": "user_service"},
            {"method": "POST", "path": "/users/login", "service": "user_service"},
            {"method": "GET", "path": "/users/<int:user_id>", "service": "user_service"},
            # Post Service
            {"method": "POST", "path": "/posts", "service": "post_service"},
            {"method": "GET", "path": "/posts", "service": "post_service"},
            {"method": "GET", "path": "/feed", "service": "post_service"},
             # Messaging Service
            {"method": "POST", "path": "/conversations", "service": "messaging_service"},
            {"method": "GET", "path": "/conversations", "service": "messaging_service"},
            # AI Sandbox
            {"method": "GET", "path": "/ai/modules", "service": "ai_sandbox_service"},
            {"method": "POST", "path": "/ai/preferences", "service": "ai_sandbox_service"}
        ]
        
        # Filter to use only defined routes if self.routes is populated
        if self.routes:
            defined_paths_methods = set((r["method"], r["path"]) for r in self.routes)
            key_endpoints = [ep for ep in key_endpoints if (ep["method"], ep["path"]) in defined_paths_methods or self.mock_mode]
        
        if not key_endpoints:
            logger.warning("No key endpoints identified for performance testing based on available routes.")
            # Fallback to a generic test if no specific endpoints are found
            key_endpoints.append({"method": "GET", "path": "/health", "service": "generic"})

        all_results = []
        load_levels = [
            {"users": 5, "duration": 10}, # Light load
            {"users": 20, "duration": 20}, # Moderate load
            # {"users": 50, "duration": 30}  # Heavy load - uncomment for more intense testing
        ]

        for endpoint in key_endpoints:
            endpoint_results = []
            for level in load_levels:
                result = self._perform_load_test_on_endpoint(endpoint, level["users"], level["duration"])
                endpoint_results.append(result)
            all_results.append({"endpoint_group": endpoint["path"], "results_by_load": endpoint_results})
        
        # Save results
        results_file = self.performance_dir / "performance_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        report_file = self._generate_performance_report(all_results)
        
        logger.info(f"Performance tests completed. Results: {results_file}, Report: {report_file}")
        return {
            "results_file": str(results_file),
            "report_file": str(report_file),
            "summary": all_results
        }

    def _generate_performance_report(self, all_results):
        report_file = self.performance_dir / "performance_test_report.md"
        with open(report_file, 'w') as f:
            f.write("# Performance Testing Report\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Mock Mode: {self.mock_mode}\n\n")

            for endpoint_group_result in all_results:
                f.write(f"## Endpoint Group: {endpoint_group_result['endpoint_group']}\n\n")
                f.write("| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |\n")
                f.write("|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|\n")
                for result in endpoint_group_result['results_by_load']:
                    f.write(f"| {result['num_users']} | {result['duration_seconds']} | {result['total_requests']} | {result['successful_requests']} | {result['failed_requests']} | {result['avg_latency_ms']:.2f} | {result['p95_latency_ms']:.2f} | {result['rps']:.2f} |\n")
                f.write("\n")
            
            f.write("## Summary & Recommendations\n\n")
            f.write("- Review endpoints with high latencies or high failure rates under load.\n")
            f.write("- Consider optimizing database queries and application logic for critical paths.\n")
            f.write("- Scale resources appropriately based on expected user load.\n")
            f.write("- If P95 latency is significantly higher than average, investigate outliers and long-tail responses.\n")

        return str(report_file)

if __name__ == "__main__":
    tester = PerformanceTester()
    tester.run_performance_tests()
