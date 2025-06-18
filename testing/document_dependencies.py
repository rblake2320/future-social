#!/usr/bin/env python3
"""
Surgical-Precision Testing - Dependency Documentation
This script documents all dependencies for the Future Social (FS) project.
"""

import os
import sys
import json
import subprocess
import platform
import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("testing/dependency_documentation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_dependency_doc")

class DependencyDocumentation:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.dependencies_file = self.test_env_dir / "dependencies.json"
        self.test_venv_dir = self.test_env_dir / "venv"
        
        logger.info(f"Dependency documentation initialized for project at {self.project_root}")

    def document_system_info(self):
        """Document system information"""
        logger.info("Documenting system information...")
        
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "python_implementation": platform.python_implementation(),
            "python_compiler": platform.python_compiler(),
            "system": platform.system(),
            "release": platform.release(),
            "node": platform.node(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"System information documented: {platform.system()} {platform.release()}")
        return system_info

    def document_service_dependencies(self):
        """Document dependencies for each service"""
        logger.info("Documenting service dependencies...")
        
        service_deps = {}
        for service_dir in ["user_service", "post_service", "messaging_service", 
                           "group_service", "ai_sandbox_service"]:
            req_file = self.project_root / "src" / service_dir / "requirements.txt"
            if req_file.exists():
                with open(req_file, 'r') as f:
                    requirements = f.read().splitlines()
                    # Filter out empty lines and comments
                    requirements = [r for r in requirements if r and not r.startswith('#')]
                    service_deps[service_dir] = requirements
                    logger.info(f"Documented {len(requirements)} dependencies for {service_dir}")
            else:
                logger.warning(f"Requirements file not found for {service_dir}")
        
        return service_deps

    def document_testing_dependencies(self):
        """Document testing dependencies"""
        logger.info("Documenting testing dependencies...")
        
        testing_deps = {
            "installed_packages": [],
            "testing_tools": []
        }
        
        # Check if virtual environment exists
        if self.test_venv_dir.exists():
            try:
                # Get all installed packages
                pip_path = self.test_venv_dir / "bin" / "pip"
                result = subprocess.run([str(pip_path), "freeze"], capture_output=True, text=True, check=True)
                testing_deps["installed_packages"] = result.stdout.splitlines()
                
                # Identify specific testing tools
                testing_tools = [
                    "pytest", "pytest-cov", "pytest-mock", "pytest-flask", 
                    "locust", "safety", "bandit", "pylint", "flake8",
                    "coverage", "requests-mock", "pytest-benchmark"
                ]
                
                for package in testing_deps["installed_packages"]:
                    for tool in testing_tools:
                        if package.lower().startswith(tool.lower()):
                            testing_deps["testing_tools"].append(package)
                
                logger.info(f"Documented {len(testing_deps['installed_packages'])} testing dependencies")
                logger.info(f"Identified {len(testing_deps['testing_tools'])} specific testing tools")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to get testing dependencies: {e}")
        else:
            logger.warning(f"Testing virtual environment not found at {self.test_venv_dir}")
        
        return testing_deps

    def document_dependency_tree(self):
        """Document dependency tree for each service"""
        logger.info("Documenting dependency trees...")
        
        dependency_trees = {}
        
        if self.test_venv_dir.exists():
            pip_path = self.test_venv_dir / "bin" / "pip"
            
            for service_dir in ["user_service", "post_service", "messaging_service", 
                               "group_service", "ai_sandbox_service"]:
                req_file = self.project_root / "src" / service_dir / "requirements.txt"
                if req_file.exists():
                    try:
                        # Use pip-tree to get dependency tree
                        result = subprocess.run(
                            [str(pip_path), "install", "pipdeptree"],
                            capture_output=True, text=True, check=True
                        )
                        
                        pipdeptree_path = self.test_venv_dir / "bin" / "pipdeptree"
                        if os.path.exists(pipdeptree_path):
                            result = subprocess.run(
                                [str(pipdeptree_path), "--json-tree"],
                                capture_output=True, text=True, check=True
                            )
                            dependency_trees[service_dir] = json.loads(result.stdout)
                            logger.info(f"Documented dependency tree for {service_dir}")
                        else:
                            logger.warning("pipdeptree not found after installation")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to get dependency tree for {service_dir}: {e}")
                        # Fallback to simple list if tree fails
                        dependency_trees[service_dir] = "Error generating dependency tree"
        
        return dependency_trees

    def document_version_constraints(self):
        """Document version constraints and potential conflicts"""
        logger.info("Analyzing version constraints...")
        
        version_constraints = {
            "potential_conflicts": [],
            "pinned_versions": {},
            "unpinned_dependencies": []
        }
        
        # Collect all version constraints across services
        all_requirements = {}
        for service_dir in ["user_service", "post_service", "messaging_service", 
                           "group_service", "ai_sandbox_service"]:
            req_file = self.project_root / "src" / service_dir / "requirements.txt"
            if req_file.exists():
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse requirement
                            parts = line.split('==')
                            if len(parts) == 2:
                                package, version = parts
                                if package in all_requirements and all_requirements[package] != version:
                                    version_constraints["potential_conflicts"].append({
                                        "package": package,
                                        "versions": [all_requirements[package], version],
                                        "services": [service for service, reqs in version_constraints["pinned_versions"].items() 
                                                    if package in reqs]
                                    })
                                all_requirements[package] = version
                                
                                # Track by service
                                if service_dir not in version_constraints["pinned_versions"]:
                                    version_constraints["pinned_versions"][service_dir] = {}
                                version_constraints["pinned_versions"][service_dir][package] = version
                            else:
                                # Unpinned dependency
                                version_constraints["unpinned_dependencies"].append(line)
        
        logger.info(f"Found {len(version_constraints['potential_conflicts'])} potential version conflicts")
        logger.info(f"Found {len(version_constraints['unpinned_dependencies'])} unpinned dependencies")
        
        return version_constraints

    def generate_dependency_report(self):
        """Generate comprehensive dependency report"""
        logger.info("Generating comprehensive dependency report...")
        
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "system_info": self.document_system_info(),
            "service_dependencies": self.document_service_dependencies(),
            "testing_dependencies": self.document_testing_dependencies(),
            "version_constraints": self.document_version_constraints(),
            "dependency_trees": self.document_dependency_tree()
        }
        
        # Save report to file
        with open(self.dependencies_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Dependency report saved to {self.dependencies_file}")
        
        # Generate human-readable summary
        summary_file = self.test_env_dir / "dependency_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# Future Social (FS) Dependency Summary\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")
            
            f.write("## System Information\n\n")
            for key, value in report["system_info"].items():
                if key != "timestamp":
                    f.write(f"- **{key}**: {value}\n")
            f.write("\n")
            
            f.write("## Service Dependencies\n\n")
            for service, deps in report["service_dependencies"].items():
                f.write(f"### {service}\n\n")
                for dep in deps:
                    f.write(f"- {dep}\n")
                f.write("\n")
            
            f.write("## Testing Tools\n\n")
            for tool in report["testing_dependencies"]["testing_tools"]:
                f.write(f"- {tool}\n")
            f.write("\n")
            
            f.write("## Potential Version Conflicts\n\n")
            if report["version_constraints"]["potential_conflicts"]:
                for conflict in report["version_constraints"]["potential_conflicts"]:
                    f.write(f"- **{conflict['package']}**: {', '.join(conflict['versions'])}\n")
                    f.write(f"  - Affected services: {', '.join(conflict['services'])}\n")
            else:
                f.write("No version conflicts detected.\n")
            f.write("\n")
            
            f.write("## Unpinned Dependencies\n\n")
            if report["version_constraints"]["unpinned_dependencies"]:
                for dep in report["version_constraints"]["unpinned_dependencies"]:
                    f.write(f"- {dep}\n")
            else:
                f.write("No unpinned dependencies found.\n")
        
        logger.info(f"Dependency summary saved to {summary_file}")
        return report

if __name__ == "__main__":
    doc = DependencyDocumentation()
    doc.generate_dependency_report()
