#!/usr/bin/env python3
"""
Surgical-Precision Testing - User Journey and Flowchart Generator
This script generates user journeys and flowcharts for the Future Social (FS) project.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("testing/user_journey.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_user_journey")

class UserJourneyGenerator:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.mapping_dir = self.test_results_dir / "element_mapping"
        self.journey_dir = self.test_results_dir / "user_journeys"
        self.journey_summary_file = self.journey_dir / "journey_summary.json"
        
        # Ensure directories exist
        self.journey_dir.mkdir(exist_ok=True, parents=True)
        
        # Load mapping data
        self.routes = self._load_json(self.mapping_dir / "api_routes.json")
        self.models = self._load_json(self.mapping_dir / "database_models.json")
        self.dependencies = self._load_json(self.mapping_dir / "service_dependencies.json")
        
        logger.info(f"User journey generator initialized for project at {self.project_root}")

    def _load_json(self, file_path):
        """Load JSON data from file"""
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

    def identify_core_user_journeys(self):
        """Identify core user journeys based on API routes"""
        logger.info("Identifying core user journeys...")
        
        # Group routes by service
        services = {}
        for route in self.routes:
            service = route["service"]
            if service not in services:
                services[service] = []
            services[service].append(route)
        
        # Define core user journeys
        journeys = []
        
        # User Authentication Journey
        if "user_service" in services:
            user_routes = services["user_service"]
            auth_journey = {
                "name": "User Authentication",
                "description": "User registration, login, and profile management",
                "steps": []
            }
            
            # Find relevant routes
            for method, path_pattern, step_name in [
                ("POST", "/register", "Register new user"),
                ("POST", "/login", "Login with credentials"),
                ("GET", "/users/", "View user profile"),
                ("PUT", "/users/", "Update user profile"),
                ("GET", "/logout", "Logout from system")
            ]:
                for route in user_routes:
                    if route["method"] == method and self._path_matches(route["path"], path_pattern):
                        auth_journey["steps"].append({
                            "name": step_name,
                            "method": route["method"],
                            "path": route["path"],
                            "service": route["service"]
                        })
            
            if auth_journey["steps"]:
                journeys.append(auth_journey)
        
        # Content Creation and Viewing Journey
        if "post_service" in services:
            post_routes = services["post_service"]
            content_journey = {
                "name": "Content Creation and Viewing",
                "description": "Creating, viewing, and interacting with posts",
                "steps": []
            }
            
            # Find relevant routes
            for method, path_pattern, step_name in [
                ("GET", "/posts", "View all posts"),
                ("POST", "/posts", "Create new post"),
                ("GET", "/posts/", "View specific post"),
                ("PUT", "/posts/", "Update post"),
                ("DELETE", "/posts/", "Delete post"),
                ("POST", "/posts//like", "Like a post"),
                ("POST", "/posts//comment", "Comment on post"),
                ("GET", "/feed", "View personalized feed")
            ]:
                for route in post_routes:
                    if route["method"] == method and self._path_matches(route["path"], path_pattern):
                        content_journey["steps"].append({
                            "name": step_name,
                            "method": route["method"],
                            "path": route["path"],
                            "service": route["service"]
                        })
            
            if content_journey["steps"]:
                journeys.append(content_journey)
        
        # Messaging Journey
        if "messaging_service" in services:
            messaging_routes = services["messaging_service"]
            messaging_journey = {
                "name": "Direct Messaging",
                "description": "Sending and receiving direct messages",
                "steps": []
            }
            
            # Find relevant routes
            for method, path_pattern, step_name in [
                ("GET", "/conversations", "View all conversations"),
                ("POST", "/conversations", "Start new conversation"),
                ("GET", "/conversations/", "View conversation"),
                ("POST", "/conversations//messages", "Send message"),
                ("GET", "/conversations//messages", "View messages"),
                ("PUT", "/conversations//read", "Mark as read")
            ]:
                for route in messaging_routes:
                    if route["method"] == method and self._path_matches(route["path"], path_pattern):
                        messaging_journey["steps"].append({
                            "name": step_name,
                            "method": route["method"],
                            "path": route["path"],
                            "service": route["service"]
                        })
            
            if messaging_journey["steps"]:
                journeys.append(messaging_journey)
        
        # Group Interaction Journey
        if "group_service" in services:
            group_routes = services["group_service"]
            group_journey = {
                "name": "Group Interaction",
                "description": "Creating, joining, and participating in groups",
                "steps": []
            }
            
            # Find relevant routes
            for method, path_pattern, step_name in [
                ("GET", "/groups", "View all groups"),
                ("POST", "/groups", "Create new group"),
                ("GET", "/groups/", "View group details"),
                ("PUT", "/groups/", "Update group"),
                ("POST", "/groups//join", "Join group"),
                ("POST", "/groups//leave", "Leave group"),
                ("POST", "/groups//posts", "Create group post"),
                ("GET", "/groups//posts", "View group posts")
            ]:
                for route in group_routes:
                    if route["method"] == method and self._path_matches(route["path"], path_pattern):
                        group_journey["steps"].append({
                            "name": step_name,
                            "method": route["method"],
                            "path": route["path"],
                            "service": route["service"]
                        })
            
            if group_journey["steps"]:
                journeys.append(group_journey)
        
        # AI Sandbox Journey
        if "ai_sandbox_service" in services:
            ai_routes = services["ai_sandbox_service"]
            ai_journey = {
                "name": "AI Sandbox Learning",
                "description": "Learning and experimenting with AI in the sandbox",
                "steps": []
            }
            
            # Find relevant routes
            for method, path_pattern, step_name in [
                ("GET", "/modules", "View learning modules"),
                ("GET", "/modules/", "Access specific module"),
                ("POST", "/progress", "Update learning progress"),
                ("GET", "/progress", "View learning progress"),
                ("POST", "/preferences", "Update AI preferences"),
                ("GET", "/preferences", "View AI preferences"),
                ("POST", "/experiment", "Run AI experiment"),
                ("GET", "/recommendations", "Get personalized recommendations")
            ]:
                for route in ai_routes:
                    if route["method"] == method and self._path_matches(route["path"], path_pattern):
                        ai_journey["steps"].append({
                            "name": step_name,
                            "method": route["method"],
                            "path": route["path"],
                            "service": route["service"]
                        })
            
            if ai_journey["steps"]:
                journeys.append(ai_journey)
        
        # Save journeys to file
        journeys_file = self.journey_dir / "core_user_journeys.json"
        with open(journeys_file, 'w') as f:
            json.dump(journeys, f, indent=2)
        
        logger.info(f"Identified {len(journeys)} core user journeys")
        return journeys

    def _path_matches(self, actual_path, pattern):
        """Check if an actual path matches a pattern with wildcards"""
        # Replace double slashes with a wildcard pattern
        if "//" in pattern:
            parts = pattern.split("//")
            return actual_path.startswith(parts[0]) and (len(parts) == 1 or actual_path.endswith(parts[1]))
        else:
            return actual_path == pattern

    def generate_user_journey_flowcharts(self, journeys):
        """Generate flowcharts for user journeys"""
        logger.info("Generating user journey flowcharts...")
        
        flowcharts = []
        
        for journey in journeys:
            # Generate PlantUML flowchart
            flowchart_file = self.journey_dir / f"{journey['name'].lower().replace(' ', '_')}_flowchart.puml"
            
            with open(flowchart_file, 'w') as f:
                f.write("@startuml\n")
                f.write("!theme plain\n")
                f.write(f"title {journey['name']} Journey\n\n")
                
                f.write("start\n")
                
                # Add steps
                prev_step = "start"
                for i, step in enumerate(journey["steps"]):
                    step_id = f"step_{i}"
                    f.write(f":{step['name']};\n")
                    
                    # Add decision points for potential errors
                    if random.random() < 0.3:  # 30% chance of adding error path
                        f.write("if (Success?) then (yes)\n")
                        if i < len(journey["steps"]) - 1:
                            f.write("  #palegreen:Success;\n")
                        else:
                            f.write("  #palegreen:Journey Complete;\n")
                        f.write("else (no)\n")
                        f.write("  #pink:Handle Error;\n")
                        f.write("  :Retry or Recover;\n")
                        f.write("endif\n")
                
                f.write("stop\n")
                f.write("@enduml\n")
            
            flowcharts.append({
                "journey": journey["name"],
                "file": str(flowchart_file)
            })
        
        # Save flowcharts metadata to file
        flowcharts_file = self.journey_dir / "user_journey_flowcharts.json"
        with open(flowcharts_file, 'w') as f:
            json.dump(flowcharts, f, indent=2)
        
        logger.info(f"Generated {len(flowcharts)} user journey flowcharts")
        return flowcharts

    def generate_test_scenarios(self, journeys):
        """Generate test scenarios for user journeys"""
        logger.info("Generating test scenarios...")
        
        scenarios = []
        
        for journey in journeys:
            journey_scenarios = {
                "journey": journey["name"],
                "scenarios": []
            }
            
            # Happy path scenario
            happy_path = {
                "name": f"Happy Path - {journey['name']}",
                "description": f"Complete {journey['name']} journey with valid inputs",
                "steps": []
            }
            
            for step in journey["steps"]:
                happy_path["steps"].append({
                    "action": step["name"],
                    "method": step["method"],
                    "path": step["path"],
                    "input": self._generate_sample_input(step),
                    "expected_result": "Success"
                })
            
            journey_scenarios["scenarios"].append(happy_path)
            
            # Error handling scenario
            error_scenario = {
                "name": f"Error Handling - {journey['name']}",
                "description": f"Test error handling in {journey['name']} journey",
                "steps": []
            }
            
            for step in journey["steps"]:
                if step["method"] in ["POST", "PUT"]:
                    error_scenario["steps"].append({
                        "action": f"Invalid {step['name']}",
                        "method": step["method"],
                        "path": step["path"],
                        "input": self._generate_invalid_input(step),
                        "expected_result": "Error"
                    })
            
            if error_scenario["steps"]:
                journey_scenarios["scenarios"].append(error_scenario)
            
            # Edge case scenario
            edge_scenario = {
                "name": f"Edge Cases - {journey['name']}",
                "description": f"Test edge cases in {journey['name']} journey",
                "steps": []
            }
            
            for step in journey["steps"]:
                if random.random() < 0.5:  # 50% chance of including step in edge case
                    edge_scenario["steps"].append({
                        "action": f"Edge case for {step['name']}",
                        "method": step["method"],
                        "path": step["path"],
                        "input": self._generate_edge_case_input(step),
                        "expected_result": "Handled appropriately"
                    })
            
            if edge_scenario["steps"]:
                journey_scenarios["scenarios"].append(edge_scenario)
            
            scenarios.append(journey_scenarios)
        
        # Save scenarios to file
        scenarios_file = self.journey_dir / "test_scenarios.json"
        with open(scenarios_file, 'w') as f:
            json.dump(scenarios, f, indent=2)
        
        logger.info(f"Generated test scenarios for {len(scenarios)} user journeys")
        return scenarios

    def _generate_sample_input(self, step):
        """Generate sample valid input for a step"""
        if "register" in step["name"].lower():
            return {
                "username": "test_user",
                "email": "test@example.com",
                "password": "SecurePassword123!"
            }
        elif "login" in step["name"].lower():
            return {
                "email": "test@example.com",
                "password": "SecurePassword123!"
            }
        elif "post" in step["name"].lower() and step["method"] == "POST":
            return {
                "title": "Sample Post Title",
                "content": "This is a sample post content for testing purposes.",
                "user_id": 1
            }
        elif "message" in step["name"].lower() and step["method"] == "POST":
            return {
                "content": "Hello, this is a test message!",
                "sender_id": 1,
                "recipient_id": 2
            }
        elif "group" in step["name"].lower() and step["method"] == "POST":
            return {
                "name": "Test Group",
                "description": "This is a test group for testing purposes.",
                "creator_id": 1
            }
        elif "preferences" in step["name"].lower() and step["method"] == "POST":
            return {
                "user_id": 1,
                "interests": ["machine_learning", "natural_language_processing", "computer_vision"],
                "difficulty_level": "intermediate"
            }
        else:
            return {"id": 1} if step["method"] in ["GET", "PUT", "DELETE"] else {}

    def _generate_invalid_input(self, step):
        """Generate invalid input for a step"""
        if "register" in step["name"].lower():
            return {
                "username": "",  # Empty username
                "email": "invalid-email",  # Invalid email format
                "password": "short"  # Too short password
            }
        elif "login" in step["name"].lower():
            return {
                "email": "nonexistent@example.com",
                "password": "WrongPassword"
            }
        elif "post" in step["name"].lower() and step["method"] == "POST":
            return {
                "title": "",  # Empty title
                "content": "X" * 10000,  # Too long content
                "user_id": -1  # Invalid user ID
            }
        elif "message" in step["name"].lower() and step["method"] == "POST":
            return {
                "content": "",  # Empty message
                "sender_id": 999,  # Non-existent sender
                "recipient_id": 999  # Non-existent recipient
            }
        else:
            return {"id": 9999}  # Non-existent ID

    def _generate_edge_case_input(self, step):
        """Generate edge case input for a step"""
        if "register" in step["name"].lower():
            return {
                "username": "a" * 100,  # Very long username
                "email": "a" * 50 + "@example.com",  # Very long email
                "password": "A" * 100 + "123!"  # Very long password
            }
        elif "post" in step["name"].lower() and step["method"] == "POST":
            return {
                "title": "a" * 255,  # Maximum length title
                "content": "a" * 5000,  # Very long content
                "user_id": 1
            }
        elif "message" in step["name"].lower() and step["method"] == "POST":
            return {
                "content": "a" * 5000,  # Very long message
                "sender_id": 1,
                "recipient_id": 1  # Sending to self
            }
        else:
            return {"id": 0}  # Edge case ID

    def generate_user_journey_documentation(self, journeys, flowcharts, scenarios):
        """Generate comprehensive documentation for user journeys"""
        logger.info("Generating user journey documentation...")
        
        doc_file = self.journey_dir / "user_journey_documentation.md"
        
        with open(doc_file, 'w') as f:
            f.write("# Future Social User Journey Documentation\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")
            
            f.write("## Overview\n\n")
            f.write("This document outlines the core user journeys in the Future Social platform, ")
            f.write("including flowcharts and test scenarios for each journey.\n\n")
            
            # Document each journey
            for i, journey in enumerate(journeys):
                f.write(f"## {i+1}. {journey['name']}\n\n")
                f.write(f"**Description**: {journey['description']}\n\n")
                
                # List steps
                f.write("### Steps\n\n")
                for j, step in enumerate(journey["steps"]):
                    f.write(f"{j+1}. **{step['name']}** - `{step['method']} {step['path']}`\n")
                f.write("\n")
                
                # Reference flowchart
                for flowchart in flowcharts:
                    if flowchart["journey"] == journey["name"]:
                        f.write(f"### Flowchart\n\n")
                        f.write(f"See flowchart file: `{os.path.basename(flowchart['file'])}`\n\n")
                        break
                
                # List test scenarios
                for journey_scenario in scenarios:
                    if journey_scenario["journey"] == journey["name"]:
                        f.write("### Test Scenarios\n\n")
                        for scenario in journey_scenario["scenarios"]:
                            f.write(f"#### {scenario['name']}\n\n")
                            f.write(f"**Description**: {scenario['description']}\n\n")
                            f.write("**Steps**:\n\n")
                            for step in scenario["steps"]:
                                f.write(f"- {step['action']} (`{step['method']} {step['path']}`)\n")
                                f.write(f"  - Input: `{json.dumps(step['input'])}`\n")
                                f.write(f"  - Expected: {step['expected_result']}\n")
                            f.write("\n")
                        break
            
            # Add testing recommendations
            f.write("## Testing Recommendations\n\n")
            f.write("1. **Test each journey independently** - Ensure each journey can be completed in isolation\n")
            f.write("2. **Test journeys in sequence** - Test multiple journeys in sequence to ensure proper state management\n")
            f.write("3. **Validate error handling** - Ensure all error cases are properly handled and reported\n")
            f.write("4. **Test edge cases** - Validate system behavior with edge case inputs\n")
            f.write("5. **Test performance** - Measure response times for each step in the journeys\n")
            f.write("6. **Test concurrency** - Ensure journeys work correctly when executed concurrently by multiple users\n")
        
        logger.info(f"User journey documentation generated: {doc_file}")
        return doc_file

    def run_generation(self):
        """Run the complete user journey generation process"""
        logger.info("Starting user journey generation...")
        
        try:
            # Identify core user journeys
            journeys = self.identify_core_user_journeys()
            
            # Generate flowcharts
            flowcharts = self.generate_user_journey_flowcharts(journeys)
            
            # Generate test scenarios
            scenarios = self.generate_test_scenarios(journeys)
            
            # Generate documentation
            doc_file = self.generate_user_journey_documentation(journeys, flowcharts, scenarios)
            
            # Generate summary
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "journeys_count": len(journeys),
                "flowcharts_count": len(flowcharts),
                "scenarios_count": sum(len(js["scenarios"]) for js in scenarios),
                "artifacts": {
                    "core_user_journeys": "core_user_journeys.json",
                    "user_journey_flowcharts": "user_journey_flowcharts.json",
                    "test_scenarios": "test_scenarios.json",
                    "documentation": "user_journey_documentation.md"
                }
            }
            
            # Save summary to file
            with open(self.journey_summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"User journey generation completed: {len(journeys)} journeys, {len(flowcharts)} flowcharts")
            return summary
            
        except Exception as e:
            logger.error(f"User journey generation failed: {e}")
            raise

if __name__ == "__main__":
    generator = UserJourneyGenerator()
    generator.run_generation()
