#!/usr/bin/env python3
"""
Surgical-Precision Testing - API Endpoint and Interactive Element Mapping
This script maps all API endpoints and interactive elements in the Future Social (FS) project.
"""

import os
import sys
import json
import re
import logging
import datetime
from pathlib import Path
import importlib.util
import inspect
import ast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("testing/element_mapping.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_element_mapping")

class ElementMapper:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.mapping_dir = self.test_results_dir / "element_mapping"
        self.mapping_summary_file = self.mapping_dir / "mapping_summary.json"
        
        # Ensure directories exist
        self.mapping_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Element mapping initialized for project at {self.project_root}")

    def map_flask_routes(self):
        """Map all Flask routes in the project"""
        logger.info("Mapping Flask routes...")
        
        routes = []
        
        # Look for Flask app files in each service directory
        service_dirs = ["user_service", "post_service", "messaging_service", 
                       "group_service", "ai_sandbox_service"]
        
        for service_dir in service_dirs:
            service_path = self.project_root / "src" / service_dir
            app_file = service_path / "app.py"
            
            if not app_file.exists():
                logger.warning(f"App file not found for {service_dir}")
                continue
            
            # Parse the app file to extract routes
            service_routes = self._extract_flask_routes_from_file(app_file, service_dir)
            routes.extend(service_routes)
        
        # Save routes to file
        routes_file = self.mapping_dir / "api_routes.json"
        with open(routes_file, 'w') as f:
            json.dump(routes, f, indent=2)
        
        logger.info(f"Found {len(routes)} API routes across {len(service_dirs)} services")
        return routes

    def _extract_flask_routes_from_file(self, file_path, service_name):
        """Extract Flask routes from a Python file using AST parsing"""
        routes = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the file
            tree = ast.parse(content)
            
            # Find route decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        route_info = None
                        
                        # Check for @app.route or @blueprint.route
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == 'route':
                                # Extract route path
                                if decorator.args:
                                    route_path = self._extract_string_value(decorator.args[0])
                                    
                                    # Extract HTTP methods
                                    methods = ["GET"]  # Default method
                                    for keyword in decorator.keywords:
                                        if keyword.arg == 'methods':
                                            if isinstance(keyword.value, ast.List):
                                                methods = [self._extract_string_value(m) for m in keyword.value.elts]
                                    
                                    # Create route info
                                    for method in methods:
                                        route_info = {
                                            "service": service_name,
                                            "path": route_path,
                                            "method": method,
                                            "function": node.name,
                                            "file": str(file_path)
                                        }
                                        routes.append(route_info)
            
            # Also look for Flask-RESTful resources
            restful_resources = self._extract_flask_restful_resources(tree, file_path, service_name)
            routes.extend(restful_resources)
            
            return routes
        
        except Exception as e:
            logger.error(f"Error extracting routes from {file_path}: {e}")
            return []

    def _extract_flask_restful_resources(self, tree, file_path, service_name):
        """Extract Flask-RESTful resources from AST"""
        routes = []
        
        # Look for api.add_resource calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == 'add_resource' and len(node.args) >= 2:
                    resource_class = self._extract_name(node.args[0])
                    route_path = self._extract_string_value(node.args[1])
                    
                    # Find the resource class methods (get, post, put, delete)
                    resource_methods = self._find_resource_methods(tree, resource_class)
                    
                    for method in resource_methods:
                        route_info = {
                            "service": service_name,
                            "path": route_path,
                            "method": method.upper(),
                            "function": f"{resource_class}.{method}",
                            "file": str(file_path),
                            "type": "restful"
                        }
                        routes.append(route_info)
        
        return routes

    def _find_resource_methods(self, tree, class_name):
        """Find HTTP methods implemented in a Flask-RESTful resource class"""
        methods = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                            methods.append(item.name)
        
        return methods or ['get']  # Default to GET if no methods found

    def _extract_string_value(self, node):
        """Extract string value from an AST node"""
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _extract_name(self, node):
        """Extract name from an AST node"""
        if isinstance(node, ast.Name):
            return node.id
        return None

    def map_database_models(self):
        """Map all database models in the project"""
        logger.info("Mapping database models...")
        
        models = []
        
        # Look for model files in each service directory
        service_dirs = ["user_service", "post_service", "messaging_service", 
                       "group_service", "ai_sandbox_service"]
        
        for service_dir in service_dirs:
            service_path = self.project_root / "src" / service_dir
            model_file = service_path / "models.py"
            
            if not model_file.exists():
                logger.warning(f"Model file not found for {service_dir}")
                continue
            
            # Parse the model file to extract models
            service_models = self._extract_models_from_file(model_file, service_dir)
            models.extend(service_models)
        
        # Save models to file
        models_file = self.mapping_dir / "database_models.json"
        with open(models_file, 'w') as f:
            json.dump(models, f, indent=2)
        
        logger.info(f"Found {len(models)} database models across {len(service_dirs)} services")
        return models

    def _extract_models_from_file(self, file_path, service_name):
        """Extract SQLAlchemy models from a Python file using AST parsing"""
        models = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the file
            tree = ast.parse(content)
            
            # Find model classes (inheriting from db.Model)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    is_model = False
                    
                    # Check if class inherits from db.Model
                    for base in node.bases:
                        if isinstance(base, ast.Attribute) and base.attr == 'Model':
                            is_model = True
                            break
                    
                    if is_model:
                        # Extract model fields
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_name = target.id
                                        field_type = None
                                        
                                        # Try to extract field type
                                        if isinstance(item.value, ast.Call):
                                            if isinstance(item.value.func, ast.Attribute):
                                                field_type = item.value.func.attr
                                            elif isinstance(item.value.func, ast.Name):
                                                field_type = item.value.func.id
                                        
                                        if field_name not in ['__tablename__', 'query']:
                                            fields.append({
                                                "name": field_name,
                                                "type": field_type
                                            })
                        
                        # Create model info
                        model_info = {
                            "service": service_name,
                            "name": node.name,
                            "fields": fields,
                            "file": str(file_path)
                        }
                        models.append(model_info)
            
            return models
        
        except Exception as e:
            logger.error(f"Error extracting models from {file_path}: {e}")
            return []

    def map_service_dependencies(self):
        """Map dependencies between services"""
        logger.info("Mapping service dependencies...")
        
        dependencies = {}
        
        # Look for service imports in each service directory
        service_dirs = ["user_service", "post_service", "messaging_service", 
                       "group_service", "ai_sandbox_service"]
        
        for service_dir in service_dirs:
            service_path = self.project_root / "src" / service_dir
            dependencies[service_dir] = []
            
            # Check all Python files in the service directory
            for py_file in service_path.glob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                    
                    # Look for imports from other services
                    for other_service in service_dirs:
                        if other_service != service_dir and f"from src.{other_service}" in content:
                            if other_service not in dependencies[service_dir]:
                                dependencies[service_dir].append(other_service)
                except Exception as e:
                    logger.error(f"Error checking imports in {py_file}: {e}")
        
        # Save dependencies to file
        dependencies_file = self.mapping_dir / "service_dependencies.json"
        with open(dependencies_file, 'w') as f:
            json.dump(dependencies, f, indent=2)
        
        # Count total dependencies
        total_deps = sum(len(deps) for deps in dependencies.values())
        logger.info(f"Found {total_deps} dependencies between services")
        return dependencies

    def generate_api_documentation(self, routes):
        """Generate API documentation from routes"""
        logger.info("Generating API documentation...")
        
        # Group routes by service
        services = {}
        for route in routes:
            service = route["service"]
            if service not in services:
                services[service] = []
            services[service].append(route)
        
        # Generate markdown documentation
        doc_file = self.mapping_dir / "api_documentation.md"
        with open(doc_file, 'w') as f:
            f.write("# Future Social API Documentation\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")
            
            for service, service_routes in services.items():
                f.write(f"## {service.replace('_', ' ').title()}\n\n")
                
                # Group routes by path
                paths = {}
                for route in service_routes:
                    path = route["path"]
                    if path not in paths:
                        paths[path] = []
                    paths[path].append(route)
                
                for path, path_routes in paths.items():
                    f.write(f"### {path}\n\n")
                    
                    for route in path_routes:
                        f.write(f"#### {route['method']}\n\n")
                        f.write(f"- **Function**: `{route['function']}`\n")
                        f.write(f"- **File**: `{route['file']}`\n\n")
                    
                    f.write("\n")
        
        logger.info(f"API documentation generated: {doc_file}")
        return doc_file

    def generate_database_diagram(self, models):
        """Generate database diagram from models"""
        logger.info("Generating database diagram...")
        
        # Generate PlantUML diagram
        diagram_file = self.mapping_dir / "database_diagram.puml"
        with open(diagram_file, 'w') as f:
            f.write("@startuml\n")
            f.write("!theme plain\n")
            f.write("title Future Social Database Schema\n\n")
            
            # Define all entities
            for model in models:
                f.write(f"entity \"{model['name']}\" as {model['name']} {{\n")
                for field in model['fields']:
                    f.write(f"  {field['name']}: {field['type'] or 'unknown'}\n")
                f.write("}\n\n")
            
            # Define relationships (based on field names)
            for model in models:
                for field in model['fields']:
                    if field['name'].endswith('_id'):
                        related_model = field['name'][:-3]  # Remove _id suffix
                        # Check if the related model exists
                        if any(m['name'] == related_model for m in models):
                            f.write(f"{model['name']} }}-- {related_model}\n")
            
            f.write("@enduml\n")
        
        logger.info(f"Database diagram generated: {diagram_file}")
        return diagram_file

    def run_mapping(self):
        """Run the complete element mapping process"""
        logger.info("Starting element mapping...")
        
        try:
            # Map API routes
            routes = self.map_flask_routes()
            
            # Map database models
            models = self.map_database_models()
            
            # Map service dependencies
            dependencies = self.map_service_dependencies()
            
            # Generate API documentation
            api_doc = self.generate_api_documentation(routes)
            
            # Generate database diagram
            db_diagram = self.generate_database_diagram(models)
            
            # Generate summary
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "routes_count": len(routes),
                "models_count": len(models),
                "services": list(dependencies.keys()),
                "artifacts": {
                    "api_routes": "api_routes.json",
                    "database_models": "database_models.json",
                    "service_dependencies": "service_dependencies.json",
                    "api_documentation": "api_documentation.md",
                    "database_diagram": "database_diagram.puml"
                }
            }
            
            # Save summary to file
            with open(self.mapping_summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Element mapping completed: {len(routes)} routes, {len(models)} models")
            return summary
            
        except Exception as e:
            logger.error(f"Element mapping failed: {e}")
            raise

if __name__ == "__main__":
    mapper = ElementMapper()
    mapper.run_mapping()
