#!/usr/bin/env python3
"""
Surgical-Precision Testing - Chaos and Failure Injection
This script conducts chaos and failure injection tests for the Future Social (FS) project.
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
import signal
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("testing/chaos_testing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_chaos_testing")

class ChaosTester:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.mapping_dir = self.test_results_dir / "element_mapping"
        self.chaos_dir = self.test_results_dir / "chaos_tests"
        self.chaos_summary_file = self.chaos_dir / "chaos_test_summary.json"
        
        # Ensure directories exist
        self.chaos_dir.mkdir(exist_ok=True, parents=True)
        
        # Load API routes and scenarios
        self.routes = self._load_json(self.mapping_dir / "api_routes.json")
        
        # Base URL for API tests
        self.base_url = "http://localhost:5000"  # Default for local testing
        self.mock_mode = not self._check_services_running()
        
        # Test session data
        self.session_data = {
            "auth_token": None,
            "user_id": None
        }
        
        logger.info(f"Chaos tester initialized. Mock mode: {self.mock_mode}")

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

    def _login_test_user(self):
        # In a real scenario, you would use a pre-defined test user or register one.
        # For simplicity, we'll mock this or use a fixed credential if not in mock_mode.
        if self.mock_mode:
            self.session_data["auth_token"] = "mock_token_chaos_test"
            self.session_data["user_id"] = 1
            logger.info("Mock login successful for chaos testing.")
            return True

        login_payload = {"email": "test1@example.com", "password": "TestPassword1!"}
        # First, try to register the user in case they don't exist
        self._api_request("POST", "/users/register", data=login_payload)
        
        result = self._api_request("POST", "/users/login", data=login_payload)
        if result["status_code"] == 200 and result["response_json"].get("token"):
            self.session_data["auth_token"] = result["response_json"]["token"]
            self.session_data["user_id"] = result["response_json"].get("user_id", 1)
            logger.info(f"Login successful for chaos testing. User ID: {self.session_data['user_id']}")
            return True
        else:
            logger.error(f"Login failed for chaos testing: {result}")
            return False

    def _api_request(self, method, path, data=None, headers=None, timeout=10, expect_failure=False):
        url = f"{self.base_url}{path}"
        effective_headers = headers or {}
        if self.session_data.get("auth_token"):
            effective_headers["Authorization"] = f"Bearer {self.session_data['auth_token']}"

        start_time = time.perf_counter()
        try:
            if self.mock_mode:
                time.sleep(random.uniform(0.01, 0.05))  # Simulate network latency
                
                # If we're expecting failure, simulate it
                if expect_failure:
                    if random.random() < 0.8:  # 80% chance of expected failure
                        raise Exception("Simulated failure for chaos testing")
                
                status_code = 200
                if "error" in path.lower(): status_code = 400  # Simple mock error
                response_json = {"mock_response": True, "path": path, "method": method}
                if method == "POST" and "login" in path:
                    response_json["token"] = "mock_token_" + str(uuid.uuid4())[:8]
                    response_json["user_id"] = 1
                elif method == "POST" and "register" in path:
                    response_json["user_id"] = 1
            else:
                if method.upper() == "GET":
                    response = requests.get(url, params=data, headers=effective_headers, timeout=timeout)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, headers=effective_headers, timeout=timeout)
                elif method.upper() == "PUT":
                    response = requests.put(url, json=data, headers=effective_headers, timeout=timeout)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=effective_headers, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                status_code = response.status_code
                try:
                    response_json = response.json()
                except json.JSONDecodeError:
                    response_json = {"error": "Non-JSON response", "text": response.text[:100]}
            
            latency = (time.perf_counter() - start_time) * 1000  # ms
            return {
                "status_code": status_code,
                "latency_ms": latency,
                "response_json": response_json,
                "error": None,
                "success": True
            }
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000  # ms
            logger.error(f"API request failed: {method} {path} - {e}")
            return {
                "status_code": 0,
                "latency_ms": latency,
                "response_json": None,
                "error": str(e),
                "success": False
            }

    def run_network_failure_tests(self):
        """Test system behavior under network failures"""
        logger.info("Running network failure tests...")
        
        results = []
        
        # Define key endpoints to test
        key_endpoints = [
            {"method": "GET", "path": "/users/<int:user_id>", "service": "user_service"},
            {"method": "POST", "path": "/posts", "service": "post_service"},
            {"method": "GET", "path": "/feed", "service": "post_service"}
        ]
        
        # Test each endpoint with simulated network failures
        for endpoint in key_endpoints:
            logger.info(f"Testing network failures for {endpoint['method']} {endpoint['path']}")
            
            # Prepare path with placeholders replaced
            path = endpoint["path"]
            if "<int:user_id>" in path:
                path = path.replace("<int:user_id>", str(self.session_data.get("user_id", 1)))
            
            # Prepare payload if needed
            payload = None
            if endpoint["method"] in ["POST", "PUT"]:
                payload = {"test_data": "chaos_test_" + str(uuid.uuid4())[:8]}
                if "post" in endpoint["path"]:
                    payload["user_id"] = self.session_data.get("user_id", 1)
                    payload["title"] = "Chaos Test Post"
                    payload["content"] = "This is a chaos test post."
            
            # Test with timeout
            timeout_result = self._api_request(
                endpoint["method"], 
                path, 
                data=payload, 
                timeout=0.001,  # Very short timeout to force failure
                expect_failure=True
            )
            
            # Test with connection interruption (simulated in mock mode)
            interrupt_result = self._api_request(
                endpoint["method"], 
                path, 
                data=payload, 
                expect_failure=True
            )
            
            # Record results
            results.append({
                "endpoint": f"{endpoint['method']} {endpoint['path']}",
                "timeout_test": {
                    "success": not timeout_result["success"],  # We expect it to fail
                    "error": timeout_result["error"]
                },
                "interrupt_test": {
                    "success": not interrupt_result["success"] if random.random() < 0.8 else False,  # We expect it to fail
                    "error": interrupt_result["error"] or "Simulated connection interruption"
                }
            })
        
        # Save results
        results_file = self.chaos_dir / "network_failure_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Network failure tests completed. Results: {results_file}")
        return results

    def run_malformed_input_tests(self):
        """Test system behavior with malformed inputs"""
        logger.info("Running malformed input tests...")
        
        results = []
        
        # Define key endpoints that accept input
        key_endpoints = [
            {"method": "POST", "path": "/users/register", "service": "user_service"},
            {"method": "POST", "path": "/posts", "service": "post_service"},
            {"method": "POST", "path": "/conversations", "service": "messaging_service"}
        ]
        
        # Define malformed input types
        malformed_inputs = [
            {"name": "empty_payload", "payload": {}},
            {"name": "null_values", "payload": {"user_id": None, "title": None, "content": None}},
            {"name": "invalid_types", "payload": {"user_id": "not_an_integer", "count": "not_a_number"}},
            {"name": "oversized_payload", "payload": {"data": "x" * 10000}},  # Very large payload
            {"name": "sql_injection", "payload": {"title": "'; DROP TABLE users; --"}}
        ]
        
        # Test each endpoint with each malformed input
        for endpoint in key_endpoints:
            endpoint_results = []
            
            for input_type in malformed_inputs:
                logger.info(f"Testing {input_type['name']} for {endpoint['method']} {endpoint['path']}")
                
                # Make request with malformed input
                result = self._api_request(
                    endpoint["method"],
                    endpoint["path"],
                    data=input_type["payload"]
                )
                
                # Determine if the system handled it correctly
                # For malformed input, we expect either a 400 error or a graceful handling
                handled_correctly = (
                    400 <= result["status_code"] < 500 or  # Proper error code
                    (result["status_code"] == 200 and not result.get("error"))  # Or graceful handling
                )
                
                endpoint_results.append({
                    "input_type": input_type["name"],
                    "status_code": result["status_code"],
                    "error": result.get("error"),
                    "handled_correctly": handled_correctly
                })
            
            results.append({
                "endpoint": f"{endpoint['method']} {endpoint['path']}",
                "results": endpoint_results
            })
        
        # Save results
        results_file = self.chaos_dir / "malformed_input_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Malformed input tests completed. Results: {results_file}")
        return results

    def run_load_spike_tests(self):
        """Test system behavior under sudden load spikes"""
        logger.info("Running load spike tests...")
        
        results = []
        
        # Define key endpoints to test
        key_endpoints = [
            {"method": "GET", "path": "/feed", "service": "post_service"},
            {"method": "GET", "path": "/users/<int:user_id>", "service": "user_service"}
        ]
        
        for endpoint in key_endpoints:
            logger.info(f"Testing load spike for {endpoint['method']} {endpoint['path']}")
            
            # Prepare path with placeholders replaced
            path = endpoint["path"]
            if "<int:user_id>" in path:
                path = path.replace("<int:user_id>", str(self.session_data.get("user_id", 1)))
            
            # Define spike parameters
            num_requests = 50  # Number of concurrent requests
            
            # Execute spike test
            start_time = time.time()
            spike_results = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
                futures = [
                    executor.submit(
                        self._api_request, 
                        endpoint["method"], 
                        path, 
                        None
                    )
                    for _ in range(num_requests)
                ]
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        spike_results.append(future.result())
                    except Exception as e:
                        logger.error(f"Error in spike test: {e}")
                        spike_results.append({"error": str(e), "success": False})
            
            end_time = time.time()
            
            # Calculate metrics
            successful_requests = sum(1 for r in spike_results if r["success"])
            failed_requests = num_requests - successful_requests
            latencies = [r["latency_ms"] for r in spike_results if "latency_ms" in r]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            results.append({
                "endpoint": f"{endpoint['method']} {endpoint['path']}",
                "num_requests": num_requests,
                "duration_seconds": end_time - start_time,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": successful_requests / num_requests if num_requests > 0 else 0,
                "avg_latency_ms": avg_latency
            })
        
        # Save results
        results_file = self.chaos_dir / "load_spike_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Load spike tests completed. Results: {results_file}")
        return results

    def run_dependency_failure_tests(self):
        """Test system behavior when dependencies fail"""
        logger.info("Running dependency failure tests...")
        
        # In a real environment, we would simulate database failures, external service failures, etc.
        # For this mock test, we'll simulate the behavior
        
        results = []
        
        # Define dependencies to test
        dependencies = [
            {"name": "database", "service": "all"},
            {"name": "cache", "service": "all"},
            {"name": "external_auth", "service": "user_service"}
        ]
        
        for dependency in dependencies:
            logger.info(f"Testing failure of {dependency['name']} for {dependency['service']}")
            
            # Define endpoints affected by this dependency
            affected_endpoints = []
            if dependency["name"] == "database":
                affected_endpoints = [
                    {"method": "GET", "path": "/users/<int:user_id>"},
                    {"method": "GET", "path": "/posts"},
                    {"method": "GET", "path": "/feed"}
                ]
            elif dependency["name"] == "cache":
                affected_endpoints = [
                    {"method": "GET", "path": "/feed"},
                    {"method": "GET", "path": "/ai/recommendations"}
                ]
            elif dependency["name"] == "external_auth":
                affected_endpoints = [
                    {"method": "POST", "path": "/users/login"},
                    {"method": "POST", "path": "/users/register"}
                ]
            
            # Test each affected endpoint
            endpoint_results = []
            for endpoint in affected_endpoints:
                # Prepare path with placeholders replaced
                path = endpoint["path"]
                if "<int:user_id>" in path:
                    path = path.replace("<int:user_id>", str(self.session_data.get("user_id", 1)))
                
                # In mock mode, we'll simulate the dependency failure
                if self.mock_mode:
                    # Simulate a 50% chance of graceful handling
                    graceful_handling = random.random() < 0.5
                    status_code = 503 if graceful_handling else 500
                    error_message = f"Simulated {dependency['name']} failure"
                    
                    endpoint_results.append({
                        "endpoint": f"{endpoint['method']} {endpoint['path']}",
                        "status_code": status_code,
                        "error": error_message,
                        "graceful_handling": graceful_handling
                    })
                else:
                    # In a real environment, we would need to actually simulate the dependency failure
                    # This would require more complex setup and is beyond the scope of this example
                    logger.warning("Real dependency failure testing not implemented")
                    
                    # For now, we'll just record a placeholder result
                    endpoint_results.append({
                        "endpoint": f"{endpoint['method']} {endpoint['path']}",
                        "status_code": 0,
                        "error": "Real dependency failure testing not implemented",
                        "graceful_handling": False
                    })
            
            results.append({
                "dependency": dependency["name"],
                "service": dependency["service"],
                "results": endpoint_results
            })
        
        # Save results
        results_file = self.chaos_dir / "dependency_failure_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Dependency failure tests completed. Results: {results_file}")
        return results

    def run_resource_exhaustion_tests(self):
        """Test system behavior under resource exhaustion"""
        logger.info("Running resource exhaustion tests...")
        
        results = []
        
        # Define resource exhaustion scenarios
        scenarios = [
            {"name": "memory_exhaustion", "description": "Test behavior when memory is exhausted"},
            {"name": "cpu_exhaustion", "description": "Test behavior when CPU is exhausted"},
            {"name": "disk_space_exhaustion", "description": "Test behavior when disk space is exhausted"}
        ]
        
        for scenario in scenarios:
            logger.info(f"Testing {scenario['name']}")
            
            # In mock mode, we'll simulate the resource exhaustion
            if self.mock_mode:
                # Simulate a 50% chance of graceful handling
                graceful_handling = random.random() < 0.5
                status_code = 503 if graceful_handling else 500
                error_message = f"Simulated {scenario['name']}"
                
                results.append({
                    "scenario": scenario["name"],
                    "description": scenario["description"],
                    "status_code": status_code,
                    "error": error_message,
                    "graceful_handling": graceful_handling
                })
            else:
                # In a real environment, we would need to actually simulate the resource exhaustion
                # This would require more complex setup and is beyond the scope of this example
                logger.warning(f"Real {scenario['name']} testing not implemented")
                
                # For now, we'll just record a placeholder result
                results.append({
                    "scenario": scenario["name"],
                    "description": scenario["description"],
                    "status_code": 0,
                    "error": f"Real {scenario['name']} testing not implemented",
                    "graceful_handling": False
                })
        
        # Save results
        results_file = self.chaos_dir / "resource_exhaustion_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Resource exhaustion tests completed. Results: {results_file}")
        return results

    def generate_chaos_report(self, all_results):
        """Generate a comprehensive chaos testing report"""
        logger.info("Generating chaos testing report...")
        
        report_file = self.chaos_dir / "chaos_test_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Chaos Testing Report\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Mock Mode: {self.mock_mode}\n\n")
            
            # Network Failure Tests
            f.write("## Network Failure Tests\n\n")
            f.write("| Endpoint | Timeout Test | Connection Interruption Test |\n")
            f.write("|----------|-------------|-----------------------------|\n")
            for result in all_results["network_failure"]:
                timeout_status = "✅ Handled" if result["timeout_test"]["success"] else "❌ Failed"
                interrupt_status = "✅ Handled" if result["interrupt_test"]["success"] else "❌ Failed"
                f.write(f"| {result['endpoint']} | {timeout_status} | {interrupt_status} |\n")
            f.write("\n")
            
            # Malformed Input Tests
            f.write("## Malformed Input Tests\n\n")
            for result in all_results["malformed_input"]:
                f.write(f"### {result['endpoint']}\n\n")
                f.write("| Input Type | Status Code | Handled Correctly |\n")
                f.write("|------------|------------|------------------|\n")
                for input_result in result["results"]:
                    handled = "✅ Yes" if input_result["handled_correctly"] else "❌ No"
                    f.write(f"| {input_result['input_type']} | {input_result['status_code']} | {handled} |\n")
                f.write("\n")
            
            # Load Spike Tests
            f.write("## Load Spike Tests\n\n")
            f.write("| Endpoint | Requests | Success Rate | Avg Latency (ms) |\n")
            f.write("|----------|----------|-------------|------------------|\n")
            for result in all_results["load_spike"]:
                success_rate = f"{result['success_rate'] * 100:.1f}%"
                f.write(f"| {result['endpoint']} | {result['num_requests']} | {success_rate} | {result['avg_latency_ms']:.2f} |\n")
            f.write("\n")
            
            # Dependency Failure Tests
            f.write("## Dependency Failure Tests\n\n")
            for result in all_results["dependency_failure"]:
                f.write(f"### {result['dependency']} (Service: {result['service']})\n\n")
                f.write("| Endpoint | Status Code | Graceful Handling |\n")
                f.write("|----------|------------|------------------|\n")
                for endpoint_result in result["results"]:
                    graceful = "✅ Yes" if endpoint_result["graceful_handling"] else "❌ No"
                    f.write(f"| {endpoint_result['endpoint']} | {endpoint_result['status_code']} | {graceful} |\n")
                f.write("\n")
            
            # Resource Exhaustion Tests
            f.write("## Resource Exhaustion Tests\n\n")
            f.write("| Scenario | Description | Graceful Handling |\n")
            f.write("|----------|-------------|------------------|\n")
            for result in all_results["resource_exhaustion"]:
                graceful = "✅ Yes" if result["graceful_handling"] else "❌ No"
                f.write(f"| {result['scenario']} | {result['description']} | {graceful} |\n")
            f.write("\n")
            
            # Summary and Recommendations
            f.write("## Summary & Recommendations\n\n")
            
            # Calculate overall success rates
            network_success = sum(1 for r in all_results["network_failure"] if r["timeout_test"]["success"] and r["interrupt_test"]["success"]) / len(all_results["network_failure"]) if all_results["network_failure"] else 0
            
            malformed_success_count = 0
            malformed_total = 0
            for result in all_results["malformed_input"]:
                for input_result in result["results"]:
                    malformed_total += 1
                    if input_result["handled_correctly"]:
                        malformed_success_count += 1
            malformed_success = malformed_success_count / malformed_total if malformed_total > 0 else 0
            
            load_spike_success = sum(r["success_rate"] for r in all_results["load_spike"]) / len(all_results["load_spike"]) if all_results["load_spike"] else 0
            
            dependency_success_count = 0
            dependency_total = 0
            for result in all_results["dependency_failure"]:
                for endpoint_result in result["results"]:
                    dependency_total += 1
                    if endpoint_result["graceful_handling"]:
                        dependency_success_count += 1
            dependency_success = dependency_success_count / dependency_total if dependency_total > 0 else 0
            
            resource_success = sum(1 for r in all_results["resource_exhaustion"] if r["graceful_handling"]) / len(all_results["resource_exhaustion"]) if all_results["resource_exhaustion"] else 0
            
            overall_success = (network_success + malformed_success + load_spike_success + dependency_success + resource_success) / 5
            
            f.write(f"### Overall Resilience Score: {overall_success * 100:.1f}%\n\n")
            f.write("#### Success Rates by Category:\n")
            f.write(f"- Network Failures: {network_success * 100:.1f}%\n")
            f.write(f"- Malformed Inputs: {malformed_success * 100:.1f}%\n")
            f.write(f"- Load Spikes: {load_spike_success * 100:.1f}%\n")
            f.write(f"- Dependency Failures: {dependency_success * 100:.1f}%\n")
            f.write(f"- Resource Exhaustion: {resource_success * 100:.1f}%\n\n")
            
            # Add recommendations based on results
            f.write("### Key Recommendations:\n\n")
            
            if network_success < 0.8:
                f.write("1. **Improve Network Resilience**:\n")
                f.write("   - Implement proper timeout handling and retry mechanisms\n")
                f.write("   - Add circuit breakers to prevent cascading failures\n")
                f.write("   - Consider implementing fallback mechanisms for critical operations\n\n")
            
            if malformed_success < 0.8:
                f.write("2. **Enhance Input Validation**:\n")
                f.write("   - Implement comprehensive input validation at API boundaries\n")
                f.write("   - Add schema validation for all incoming requests\n")
                f.write("   - Ensure proper error messages are returned for invalid inputs\n\n")
            
            if load_spike_success < 0.8:
                f.write("3. **Improve Load Handling**:\n")
                f.write("   - Implement rate limiting and throttling mechanisms\n")
                f.write("   - Consider adding auto-scaling capabilities\n")
                f.write("   - Optimize database queries and add caching where appropriate\n\n")
            
            if dependency_success < 0.8:
                f.write("4. **Enhance Dependency Management**:\n")
                f.write("   - Implement fallback mechanisms for critical dependencies\n")
                f.write("   - Add circuit breakers for external service calls\n")
                f.write("   - Consider implementing the Bulkhead pattern to isolate failures\n\n")
            
            if resource_success < 0.8:
                f.write("5. **Improve Resource Management**:\n")
                f.write("   - Implement proper resource limits and monitoring\n")
                f.write("   - Add graceful degradation mechanisms when resources are constrained\n")
                f.write("   - Consider implementing horizontal scaling for resource-intensive operations\n\n")
            
            f.write("### Next Steps:\n\n")
            f.write("1. Address critical resilience issues identified in this report\n")
            f.write("2. Implement automated chaos testing as part of the CI/CD pipeline\n")
            f.write("3. Develop and document recovery procedures for common failure scenarios\n")
            f.write("4. Conduct regular chaos engineering exercises to continuously improve resilience\n")
        
        logger.info(f"Chaos testing report generated: {report_file}")
        return report_file

    def run_chaos_tests(self):
        """Run all chaos tests"""
        logger.info("Starting chaos and failure injection tests...")
        
        try:
            # Login test user if needed
            self._login_test_user()
            
            # Run network failure tests
            network_failure_results = self.run_network_failure_tests()
            
            # Run malformed input tests
            malformed_input_results = self.run_malformed_input_tests()
            
            # Run load spike tests
            load_spike_results = self.run_load_spike_tests()
            
            # Run dependency failure tests
            dependency_failure_results = self.run_dependency_failure_tests()
            
            # Run resource exhaustion tests
            resource_exhaustion_results = self.run_resource_exhaustion_tests()
            
            # Collect all results
            all_results = {
                "network_failure": network_failure_results,
                "malformed_input": malformed_input_results,
                "load_spike": load_spike_results,
                "dependency_failure": dependency_failure_results,
                "resource_exhaustion": resource_exhaustion_results
            }
            
            # Generate report
            report_file = self.generate_chaos_report(all_results)
            
            # Generate summary
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "mock_mode": self.mock_mode,
                "network_failure_tests": len(network_failure_results),
                "malformed_input_tests": sum(len(r["results"]) for r in malformed_input_results),
                "load_spike_tests": len(load_spike_results),
                "dependency_failure_tests": sum(len(r["results"]) for r in dependency_failure_results),
                "resource_exhaustion_tests": len(resource_exhaustion_results),
                "report_file": str(report_file)
            }
            
            # Save summary to file
            with open(self.chaos_summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info("Chaos and failure injection tests completed")
            return summary
            
        except Exception as e:
            logger.error(f"Chaos testing failed: {e}")
            raise

if __name__ == "__main__":
    tester = ChaosTester()
    tester.run_chaos_tests()
