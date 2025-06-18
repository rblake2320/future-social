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