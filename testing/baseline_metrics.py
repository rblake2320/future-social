#!/usr/bin/env python3
"""
Surgical-Precision Testing - Baseline Metrics and Monitoring Setup
This script establishes baseline metrics and configures monitoring for the Future Social (FS) project.
"""

import os
import sys
import json
import time
import datetime
import logging
import subprocess
import psutil
import platform
from pathlib import Path
import threading
import signal
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("testing/baseline_metrics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_baseline_metrics")

class BaselineMetricsMonitoring:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.monitoring_dir = self.test_results_dir / "monitoring"
        self.baseline_metrics_file = self.test_env_dir / "baseline_metrics.json"
        self.monitoring_config_file = self.test_env_dir / "monitoring_config.json"
        
        # Ensure directories exist
        self.monitoring_dir.mkdir(exist_ok=True, parents=True)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 5  # seconds
        
        logger.info(f"Baseline metrics and monitoring initialized for project at {self.project_root}")

    def collect_code_metrics(self):
        """Collect code metrics for the project"""
        logger.info("Collecting code metrics...")
        
        code_metrics = {
            "services": {},
            "tests": {},
            "total": {
                "python_files": 0,
                "total_lines": 0,
                "code_lines": 0,
                "comment_lines": 0,
                "blank_lines": 0,
                "functions": 0,
                "classes": 0,
                "complexity": 0
            }
        }
        
        # Install radon for code metrics if not available
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "radon"], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to install radon: {e}")
        
        # Collect metrics for each service
        for service_dir in ["user_service", "post_service", "messaging_service", 
                           "group_service", "ai_sandbox_service"]:
            service_path = self.project_root / "src" / service_dir
            if service_path.exists():
                service_metrics = self._analyze_directory(service_path)
                code_metrics["services"][service_dir] = service_metrics
                
                # Add to totals
                for key in ["python_files", "total_lines", "code_lines", 
                           "comment_lines", "blank_lines", "functions", 
                           "classes", "complexity"]:
                    if key in service_metrics:
                        code_metrics["total"][key] += service_metrics[key]
        
        # Collect metrics for tests
        test_path = self.project_root / "tests"
        if test_path.exists():
            test_metrics = self._analyze_directory(test_path)
            code_metrics["tests"] = test_metrics
            
            # Add to totals
            for key in ["python_files", "total_lines", "code_lines", 
                       "comment_lines", "blank_lines", "functions", 
                       "classes", "complexity"]:
                if key in test_metrics:
                    code_metrics["total"][key] += test_metrics[key]
        
        logger.info(f"Collected code metrics: {code_metrics['total']['python_files']} files, "
                   f"{code_metrics['total']['total_lines']} lines")
        return code_metrics

    def _analyze_directory(self, directory):
        """Analyze a directory for code metrics using radon"""
        metrics = {
            "python_files": 0,
            "total_lines": 0,
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "functions": 0,
            "classes": 0,
            "complexity": 0
        }
        
        # Count files and lines
        py_files = list(directory.glob("**/*.py"))
        metrics["python_files"] = len(py_files)
        
        for py_file in py_files:
            # Count lines
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                metrics["total_lines"] += len(lines)
                
                # Simple line categorization
                for line in lines:
                    line = line.strip()
                    if not line:
                        metrics["blank_lines"] += 1
                    elif line.startswith('#'):
                        metrics["comment_lines"] += 1
                    else:
                        metrics["code_lines"] += 1
            
            # Use radon for more advanced metrics if available
            try:
                # Count functions and classes
                result = subprocess.run(
                    ["radon", "cc", "-s", str(py_file)],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0:
                    # Parse radon output
                    for line in result.stdout.splitlines():
                        if 'F ' in line:  # Function
                            metrics["functions"] += 1
                        elif 'C ' in line:  # Class
                            metrics["classes"] += 1
                        
                        # Extract complexity
                        if ' - ' in line:
                            try:
                                complexity = int(line.split(' - ')[1].strip())
                                metrics["complexity"] += complexity
                            except (ValueError, IndexError):
                                pass
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file} with radon: {e}")
        
        return metrics

    def collect_system_metrics(self):
        """Collect system metrics"""
        logger.info("Collecting system metrics...")
        
        system_metrics = {
            "timestamp": datetime.datetime.now().isoformat(),
            "cpu": {
                "count_physical": psutil.cpu_count(logical=False),
                "count_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=1),
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "network": {
                "interfaces": list(psutil.net_if_addrs().keys()),
                "connections": len(psutil.net_connections())
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
        }
        
        logger.info(f"Collected system metrics: CPU {system_metrics['cpu']['usage_percent']}%, "
                   f"Memory {system_metrics['memory']['percent']}%, "
                   f"Disk {system_metrics['disk']['percent']}%")
        return system_metrics

    def collect_database_metrics(self):
        """Collect database metrics (placeholder for actual DB metrics)"""
        logger.info("Collecting database metrics (placeholder)...")
        
        # This is a placeholder since we don't have an actual DB connection
        # In a real scenario, we would connect to the database and collect metrics
        database_metrics = {
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "placeholder",
            "note": "Actual database metrics would be collected here if DB was configured"
        }
        
        logger.info("Database metrics placeholder created")
        return database_metrics

    def collect_api_metrics(self):
        """Collect API metrics (placeholder for actual API metrics)"""
        logger.info("Collecting API metrics (placeholder)...")
        
        # This is a placeholder since we don't have actual API metrics yet
        # In a real scenario, we would analyze API endpoints and collect metrics
        api_metrics = {
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "placeholder",
            "endpoints": {
                "user_service": ["POST /users", "GET /users/{id}", "PUT /users/{id}", "DELETE /users/{id}"],
                "post_service": ["POST /posts", "GET /posts/{id}", "PUT /posts/{id}", "DELETE /posts/{id}"],
                "messaging_service": ["POST /messages", "GET /messages/{id}"],
                "group_service": ["POST /groups", "GET /groups/{id}"],
                "ai_sandbox_service": ["GET /modules", "GET /modules/{id}"]
            },
            "note": "Actual API metrics would be collected here after API testing"
        }
        
        logger.info("API metrics placeholder created")
        return api_metrics

    def establish_baseline_metrics(self):
        """Establish baseline metrics for the project"""
        logger.info("Establishing baseline metrics...")
        
        baseline = {
            "timestamp": datetime.datetime.now().isoformat(),
            "code_metrics": self.collect_code_metrics(),
            "system_metrics": self.collect_system_metrics(),
            "database_metrics": self.collect_database_metrics(),
            "api_metrics": self.collect_api_metrics()
        }
        
        # Save baseline metrics to file
        with open(self.baseline_metrics_file, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        logger.info(f"Baseline metrics established and saved to {self.baseline_metrics_file}")
        return baseline

    def setup_monitoring_config(self):
        """Set up monitoring configuration"""
        logger.info("Setting up monitoring configuration...")
        
        monitoring_config = {
            "enabled": True,
            "log_level": "INFO",
            "metrics_interval_seconds": self.monitoring_interval,
            "output_dir": str(self.monitoring_dir),
            "monitors": [
                {"type": "cpu", "enabled": True, "alert_threshold": 90},
                {"type": "memory", "enabled": True, "alert_threshold": 90},
                {"type": "disk", "enabled": True, "alert_threshold": 90},
                {"type": "network", "enabled": True}
            ]
        }
        
        # Save monitoring configuration
        with open(self.monitoring_config_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        logger.info(f"Monitoring configuration saved to {self.monitoring_config_file}")
        return monitoring_config

    def _monitoring_worker(self):
        """Worker function for the monitoring thread"""
        logger.info("Monitoring thread started")
        
        metrics_file = self.monitoring_dir / "system_metrics.jsonl"
        
        try:
            while self.monitoring_active:
                # Collect current metrics
                current_metrics = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "cpu": {
                        "percent": psutil.cpu_percent(interval=1),
                        "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
                    },
                    "memory": dict(psutil.virtual_memory()._asdict()),
                    "disk": {
                        "usage": dict(psutil.disk_usage('/')._asdict()),
                        "io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
                    },
                    "network": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None
                }
                
                # Append to metrics file
                with open(metrics_file, 'a') as f:
                    f.write(json.dumps(current_metrics) + '\n')
                
                # Check for alert conditions
                self._check_alerts(current_metrics)
                
                # Sleep until next collection
                time.sleep(self.monitoring_interval)
        except Exception as e:
            logger.error(f"Error in monitoring thread: {e}")
        finally:
            logger.info("Monitoring thread stopped")

    def _check_alerts(self, metrics):
        """Check metrics for alert conditions"""
        # Load alert thresholds from config
        try:
            with open(self.monitoring_config_file, 'r') as f:
                config = json.load(f)
                
            for monitor in config.get("monitors", []):
                if monitor.get("enabled", False) and "alert_threshold" in monitor:
                    monitor_type = monitor["type"]
                    threshold = monitor["alert_threshold"]
                    
                    if monitor_type == "cpu" and metrics["cpu"]["percent"] > threshold:
                        logger.warning(f"ALERT: CPU usage ({metrics['cpu']['percent']}%) exceeds threshold ({threshold}%)")
                    
                    elif monitor_type == "memory" and metrics["memory"]["percent"] > threshold:
                        logger.warning(f"ALERT: Memory usage ({metrics['memory']['percent']}%) exceeds threshold ({threshold}%)")
                    
                    elif monitor_type == "disk" and metrics["disk"]["usage"]["percent"] > threshold:
                        logger.warning(f"ALERT: Disk usage ({metrics['disk']['usage']['percent']}%) exceeds threshold ({threshold}%)")
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring_active:
            logger.info("Starting monitoring...")
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_worker)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            # Register cleanup handlers
            atexit.register(self.stop_monitoring)
            signal.signal(signal.SIGTERM, lambda sig, frame: self.stop_monitoring())
            signal.signal(signal.SIGINT, lambda sig, frame: self.stop_monitoring())
            
            logger.info("Monitoring started")
            return True
        else:
            logger.warning("Monitoring already active")
            return False

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self.monitoring_active:
            logger.info("Stopping monitoring...")
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            logger.info("Monitoring stopped")
            return True
        else:
            logger.warning("Monitoring not active")
            return False

    def run_setup(self):
        """Run the complete setup process"""
        logger.info("Starting baseline metrics and monitoring setup...")
        
        try:
            # Establish baseline metrics
            baseline = self.establish_baseline_metrics()
            
            # Set up monitoring configuration
            monitoring_config = self.setup_monitoring_config()
            
            # Start monitoring
            self.start_monitoring()
            
            # Create setup summary
            setup_summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success",
                "baseline_metrics_file": str(self.baseline_metrics_file),
                "monitoring_config_file": str(self.monitoring_config_file),
                "monitoring_active": self.monitoring_active,
                "monitoring_dir": str(self.monitoring_dir)
            }
            
            # Save setup summary
            with open(self.test_env_dir / "monitoring_summary.json", 'w') as f:
                json.dump(setup_summary, f, indent=2)
            
            logger.info("Baseline metrics and monitoring setup completed successfully")
            return setup_summary
            
        except Exception as e:
            logger.error(f"Baseline metrics and monitoring setup failed: {e}")
            raise

if __name__ == "__main__":
    setup = BaselineMetricsMonitoring()
    setup.run_setup()
    
    # Keep the script running to maintain monitoring
    # In a real scenario, this would be managed by a service
    try:
        logger.info("Monitoring active. Press Ctrl+C to stop...")
        while setup.monitoring_active:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        setup.stop_monitoring()
