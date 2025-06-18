#!/usr/bin/env python3
"""
Surgical-Precision Testing Environment Setup for Future Social (FS)
This script sets up an isolated testing environment for the FS project.
"""

import os
import sys
import subprocess
import json
import platform
import psutil
import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("testing/test_setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_test_setup")

class TestEnvironmentSetup:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.test_data_dir = self.test_env_dir / "test_data"
        self.baseline_metrics_file = self.test_env_dir / "baseline_metrics.json"
        self.dependencies_file = self.test_env_dir / "dependencies.json"
        
        # Ensure directories exist
        self.test_env_dir.mkdir(exist_ok=True)
        self.test_results_dir.mkdir(exist_ok=True)
        self.test_data_dir.mkdir(exist_ok=True)
        
        logger.info(f"Test environment initialized at {self.test_env_dir}")

    def create_isolated_environment(self):
        """Create an isolated testing environment"""
        logger.info("Creating isolated testing environment...")
        
        # Create a virtual environment for testing if it doesn't exist
        test_venv_dir = self.test_env_dir / "venv"
        if not test_venv_dir.exists():
            try:
                subprocess.run([sys.executable, "-m", "venv", str(test_venv_dir)], check=True)
                logger.info(f"Created virtual environment at {test_venv_dir}")
                
                # Install base requirements
                pip_path = test_venv_dir / "bin" / "pip"
                subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
                
                # Install testing tools
                testing_tools = [
                    "pytest", "pytest-cov", "pytest-mock", "pytest-flask", 
                    "locust", "safety", "bandit", "pylint", "flake8",
                    "coverage", "requests-mock", "pytest-benchmark"
                ]
                subprocess.run([str(pip_path), "install"] + testing_tools, check=True)
                logger.info(f"Installed testing tools: {', '.join(testing_tools)}")
                
                # Install project requirements from each service
                for service_dir in ["user_service", "post_service", "messaging_service", 
                                   "group_service", "ai_sandbox_service"]:
                    req_file = self.project_root / "src" / service_dir / "requirements.txt"
                    if req_file.exists():
                        subprocess.run([str(pip_path), "install", "-r", str(req_file)], check=True)
                        logger.info(f"Installed requirements from {service_dir}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create virtual environment: {e}")
                raise
        else:
            logger.info(f"Using existing virtual environment at {test_venv_dir}")
        
        return test_venv_dir

    def document_dependencies(self):
        """Document all project dependencies"""
        logger.info("Documenting project dependencies...")
        
        dependencies = {}
        
        # Document system info
        dependencies["system"] = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
        }
        
        # Document service dependencies
        dependencies["services"] = {}
        for service_dir in ["user_service", "post_service", "messaging_service", 
                           "group_service", "ai_sandbox_service"]:
            req_file = self.project_root / "src" / service_dir / "requirements.txt"
            if req_file.exists():
                with open(req_file, 'r') as f:
                    dependencies["services"][service_dir] = f.read().splitlines()
        
        # Document testing dependencies
        test_venv_dir = self.test_env_dir / "venv"
        if test_venv_dir.exists():
            try:
                pip_path = test_venv_dir / "bin" / "pip"
                result = subprocess.run([str(pip_path), "freeze"], capture_output=True, text=True, check=True)
                dependencies["testing_tools"] = result.stdout.splitlines()
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to get testing dependencies: {e}")
        
        # Save dependencies to file
        with open(self.dependencies_file, 'w') as f:
            json.dump(dependencies, f, indent=2)
        
        logger.info(f"Dependencies documented in {self.dependencies_file}")
        return dependencies

    def establish_baseline_metrics(self):
        """Establish baseline metrics for the project"""
        logger.info("Establishing baseline metrics...")
        
        baseline = {
            "timestamp": datetime.datetime.now().isoformat(),
            "code_metrics": {},
            "system_metrics": {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": dict(psutil.disk_usage("/").__dict__)
            }
        }
        
        # Count lines of code, files, etc.
        for service_dir in ["user_service", "post_service", "messaging_service", 
                           "group_service", "ai_sandbox_service"]:
            service_path = self.project_root / "src" / service_dir
            if service_path.exists():
                py_files = list(service_path.glob("**/*.py"))
                baseline["code_metrics"][service_dir] = {
                    "python_files": len(py_files),
                    "total_lines": sum(1 for f in py_files for _ in open(f)),
                }
        
        # Count test files and lines
        test_path = self.project_root / "tests"
        if test_path.exists():
            test_files = list(test_path.glob("**/*.py"))
            baseline["code_metrics"]["tests"] = {
                "test_files": len(test_files),
                "test_lines": sum(1 for f in test_files for _ in open(f)),
            }
        
        # Save baseline metrics to file
        with open(self.baseline_metrics_file, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        logger.info(f"Baseline metrics established in {self.baseline_metrics_file}")
        return baseline

    def setup_monitoring_tools(self):
        """Set up monitoring tools for the testing process"""
        logger.info("Setting up monitoring tools...")
        
        # Create monitoring configuration
        monitoring_config = {
            "enabled": True,
            "log_level": "INFO",
            "metrics_interval_seconds": 5,
            "output_dir": str(self.test_results_dir / "monitoring"),
            "monitors": [
                {"type": "cpu", "enabled": True},
                {"type": "memory", "enabled": True},
                {"type": "disk", "enabled": True},
                {"type": "network", "enabled": True}
            ]
        }
        
        # Create monitoring directory
        monitoring_dir = self.test_results_dir / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        # Save monitoring configuration
        with open(self.test_env_dir / "monitoring_config.json", 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        logger.info("Monitoring tools configured")
        return monitoring_config

    def configure_recording_capabilities(self):
        """Configure recording capabilities for test sessions"""
        logger.info("Configuring recording capabilities...")
        
        # Create recording configuration
        recording_config = {
            "screenshots": {
                "enabled": True,
                "directory": str(self.test_results_dir / "screenshots"),
                "format": "png",
                "on_failure": True,
                "on_success": False
            },
            "logs": {
                "enabled": True,
                "directory": str(self.test_results_dir / "logs"),
                "level": "DEBUG",
                "rotate": True,
                "max_size_mb": 100,
                "backup_count": 5
            },
            "api_calls": {
                "enabled": True,
                "directory": str(self.test_results_dir / "api_calls"),
                "record_request": True,
                "record_response": True,
                "mask_sensitive_data": True
            }
        }
        
        # Create recording directories
        (self.test_results_dir / "screenshots").mkdir(exist_ok=True)
        (self.test_results_dir / "logs").mkdir(exist_ok=True)
        (self.test_results_dir / "api_calls").mkdir(exist_ok=True)
        
        # Save recording configuration
        with open(self.test_env_dir / "recording_config.json", 'w') as f:
            json.dump(recording_config, f, indent=2)
        
        logger.info("Recording capabilities configured")
        return recording_config

    def run_setup(self):
        """Run the complete setup process"""
        logger.info("Starting test environment setup...")
        
        try:
            # Execute all setup steps
            test_venv = self.create_isolated_environment()
            dependencies = self.document_dependencies()
            baseline = self.establish_baseline_metrics()
            monitoring = self.setup_monitoring_tools()
            recording = self.configure_recording_capabilities()
            
            # Create setup summary
            setup_summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success",
                "test_environment": str(self.test_env_dir),
                "virtual_env": str(test_venv),
                "dependencies_file": str(self.dependencies_file),
                "baseline_metrics_file": str(self.baseline_metrics_file),
                "monitoring_config": monitoring,
                "recording_config": recording
            }
            
            # Save setup summary
            with open(self.test_env_dir / "setup_summary.json", 'w') as f:
                json.dump(setup_summary, f, indent=2)
            
            logger.info("Test environment setup completed successfully")
            return setup_summary
            
        except Exception as e:
            logger.error(f"Test environment setup failed: {e}")
            raise

if __name__ == "__main__":
    setup = TestEnvironmentSetup()
    setup.run_setup()
