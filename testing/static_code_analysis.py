#!/usr/bin/env python3
"""
Surgical-Precision Testing - Static Code Analysis and Dependency Scanning
This script performs comprehensive static analysis on the Future Social (FS) project.
"""

import os
import sys
import json
import subprocess
import logging
import datetime
import glob
from pathlib import Path
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("testing/static_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_static_analysis")

class StaticCodeAnalysis:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.analysis_dir = self.test_results_dir / "static_analysis"
        self.venv_dir = self.test_env_dir / "venv"
        self.analysis_summary_file = self.analysis_dir / "analysis_summary.json"
        
        # Ensure directories exist
        self.analysis_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Static code analysis initialized for project at {self.project_root}")

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

    def run_flake8_analysis(self):
        """Run flake8 code quality analysis"""
        logger.info("Running flake8 code quality analysis...")
        
        try:
            # Run flake8 on the src directory
            python_path = self.get_venv_python()
            output_file = self.analysis_dir / "flake8_results.txt"
            
            cmd = [
                python_path, "-m", "flake8", 
                "--output-file", str(output_file),
                "--statistics",
                "--count",
                str(self.project_root / "src")
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse the results
            error_count = 0
            warning_count = 0
            
            if output_file.exists():
                with open(output_file, 'r') as f:
                    content = f.read()
                    
                    # Count errors and warnings
                    for line in content.splitlines():
                        if ': E' in line:
                            error_count += 1
                        elif ': W' in line:
                            warning_count += 1
            
            # Generate summary
            summary = {
                "tool": "flake8",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success" if result.returncode == 0 else "issues_found",
                "error_count": error_count,
                "warning_count": warning_count,
                "output_file": str(output_file),
                "return_code": result.returncode
            }
            
            logger.info(f"Flake8 analysis completed: {error_count} errors, {warning_count} warnings")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to run flake8 analysis: {e}")
            return {
                "tool": "flake8",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_bandit_analysis(self):
        """Run bandit security analysis"""
        logger.info("Running bandit security analysis...")
        
        try:
            # Run bandit on the src directory
            python_path = self.get_venv_python()
            output_file = self.analysis_dir / "bandit_results.json"
            
            cmd = [
                python_path, "-m", "bandit",
                "-r", str(self.project_root / "src"),
                "-f", "json",
                "-o", str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse the results
            issues = {
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            if output_file.exists():
                with open(output_file, 'r') as f:
                    try:
                        data = json.load(f)
                        if "results" in data:
                            for issue in data["results"]:
                                severity = issue.get("issue_severity", "").lower()
                                if severity in issues:
                                    issues[severity] += 1
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse bandit JSON output")
            
            # Generate summary
            summary = {
                "tool": "bandit",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success" if result.returncode == 0 else "issues_found",
                "high_severity_issues": issues["high"],
                "medium_severity_issues": issues["medium"],
                "low_severity_issues": issues["low"],
                "total_issues": sum(issues.values()),
                "output_file": str(output_file),
                "return_code": result.returncode
            }
            
            logger.info(f"Bandit analysis completed: {summary['total_issues']} issues found "
                       f"(High: {issues['high']}, Medium: {issues['medium']}, Low: {issues['low']})")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to run bandit analysis: {e}")
            return {
                "tool": "bandit",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_safety_check(self):
        """Run safety dependency vulnerability check"""
        logger.info("Running safety dependency vulnerability check...")
        
        try:
            # Run safety check on all requirements files
            python_path = self.get_venv_python()
            output_file = self.analysis_dir / "safety_results.json"
            
            # Collect all requirements files
            req_files = []
            for service_dir in ["user_service", "post_service", "messaging_service", 
                               "group_service", "ai_sandbox_service"]:
                req_file = self.project_root / "src" / service_dir / "requirements.txt"
                if req_file.exists():
                    req_files.append(str(req_file))
            
            if not req_files:
                logger.warning("No requirements files found")
                return {
                    "tool": "safety",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "warning",
                    "message": "No requirements files found"
                }
            
            # Run safety check for each requirements file
            vulnerabilities = []
            
            for req_file in req_files:
                cmd = [
                    python_path, "-m", "safety", "check",
                    "-r", req_file,
                    "--json"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                try:
                    # Parse JSON output
                    if result.stdout:
                        data = json.loads(result.stdout)
                        if isinstance(data, list):
                            vulnerabilities.extend(data)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse safety JSON output for {req_file}")
            
            # Save results to file
            with open(output_file, 'w') as f:
                json.dump(vulnerabilities, f, indent=2)
            
            # Generate summary
            summary = {
                "tool": "safety",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success" if not vulnerabilities else "vulnerabilities_found",
                "vulnerability_count": len(vulnerabilities),
                "requirements_files_checked": req_files,
                "output_file": str(output_file)
            }
            
            logger.info(f"Safety check completed: {len(vulnerabilities)} vulnerabilities found")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to run safety check: {e}")
            return {
                "tool": "safety",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_pylint_analysis(self):
        """Run pylint code quality analysis"""
        logger.info("Running pylint code quality analysis...")
        
        try:
            # Install pylint if not already installed
            pip_path = self.get_venv_pip()
            subprocess.run([pip_path, "install", "pylint"], capture_output=True, check=True)
            
            # Run pylint on the src directory
            python_path = self.get_venv_python()
            output_file = self.analysis_dir / "pylint_results.txt"
            
            # Find all Python files in src
            python_files = []
            for root, _, files in os.walk(str(self.project_root / "src")):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
            
            if not python_files:
                logger.warning("No Python files found in src directory")
                return {
                    "tool": "pylint",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "warning",
                    "message": "No Python files found"
                }
            
            cmd = [
                python_path, "-m", "pylint",
                "--output-format=text",
                "--reports=y"
            ] + python_files
            
            with open(output_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            # Extract score from output
            score = None
            if output_file.exists():
                with open(output_file, 'r') as f:
                    content = f.read()
                    for line in content.splitlines():
                        if "Your code has been rated at" in line:
                            try:
                                score = float(line.split("at")[1].split("/")[0].strip())
                            except (ValueError, IndexError):
                                pass
            
            # Generate summary
            summary = {
                "tool": "pylint",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success",
                "score": score,
                "output_file": str(output_file),
                "return_code": result.returncode
            }
            
            logger.info(f"Pylint analysis completed with score: {score}/10.0")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to run pylint analysis: {e}")
            return {
                "tool": "pylint",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_radon_analysis(self):
        """Run radon code complexity analysis"""
        logger.info("Running radon code complexity analysis...")
        
        try:
            # Run radon on the src directory
            python_path = self.get_venv_python()
            cc_output_file = self.analysis_dir / "radon_cc_results.json"
            mi_output_file = self.analysis_dir / "radon_mi_results.json"
            raw_output_file = self.analysis_dir / "radon_raw_results.json"
            
            # Run cyclomatic complexity analysis
            cc_cmd = [
                python_path, "-m", "radon", "cc",
                "--json",
                str(self.project_root / "src")
            ]
            
            with open(cc_output_file, 'w') as f:
                cc_result = subprocess.run(cc_cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            # Run maintainability index analysis
            mi_cmd = [
                python_path, "-m", "radon", "mi",
                "--json",
                str(self.project_root / "src")
            ]
            
            with open(mi_output_file, 'w') as f:
                mi_result = subprocess.run(mi_cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            # Run raw metrics analysis
            raw_cmd = [
                python_path, "-m", "radon", "raw",
                "--json",
                str(self.project_root / "src")
            ]
            
            with open(raw_output_file, 'w') as f:
                raw_result = subprocess.run(raw_cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            # Parse results
            complexity_data = {}
            if cc_output_file.exists():
                with open(cc_output_file, 'r') as f:
                    try:
                        complexity_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse radon CC JSON output")
            
            # Count complexity levels
            complexity_counts = {
                "A": 0,  # Simple - good
                "B": 0,  # Slightly complex - good
                "C": 0,  # Complex - moderate
                "D": 0,  # More complex - moderate
                "E": 0,  # Very complex - bad
                "F": 0   # Extremely complex - bad
            }
            
            total_functions = 0
            
            for file_path, functions in complexity_data.items():
                for func in functions:
                    complexity = func.get("complexity", 0)
                    rank = "A"
                    if complexity > 50:
                        rank = "F"
                    elif complexity > 30:
                        rank = "E"
                    elif complexity > 20:
                        rank = "D"
                    elif complexity > 10:
                        rank = "C"
                    elif complexity > 5:
                        rank = "B"
                    
                    complexity_counts[rank] += 1
                    total_functions += 1
            
            # Generate summary
            summary = {
                "tool": "radon",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success",
                "total_functions": total_functions,
                "complexity_distribution": complexity_counts,
                "high_complexity_percentage": round(((complexity_counts["E"] + complexity_counts["F"]) / total_functions * 100) if total_functions > 0 else 0, 2),
                "output_files": {
                    "cyclomatic_complexity": str(cc_output_file),
                    "maintainability_index": str(mi_output_file),
                    "raw_metrics": str(raw_output_file)
                }
            }
            
            logger.info(f"Radon analysis completed: {total_functions} functions analyzed")
            logger.info(f"Complexity distribution: A:{complexity_counts['A']}, B:{complexity_counts['B']}, "
                       f"C:{complexity_counts['C']}, D:{complexity_counts['D']}, "
                       f"E:{complexity_counts['E']}, F:{complexity_counts['F']}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to run radon analysis: {e}")
            return {
                "tool": "radon",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_mypy_analysis(self):
        """Run mypy type checking"""
        logger.info("Running mypy type checking...")
        
        try:
            # Install mypy if not already installed
            pip_path = self.get_venv_pip()
            subprocess.run([pip_path, "install", "mypy"], capture_output=True, check=True)
            
            # Run mypy on the src directory
            python_path = self.get_venv_python()
            output_file = self.analysis_dir / "mypy_results.txt"
            
            cmd = [
                python_path, "-m", "mypy",
                "--ignore-missing-imports",
                str(self.project_root / "src")
            ]
            
            with open(output_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            # Count errors
            error_count = 0
            if output_file.exists():
                with open(output_file, 'r') as f:
                    for line in f:
                        if ": error:" in line:
                            error_count += 1
            
            # Generate summary
            summary = {
                "tool": "mypy",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success" if result.returncode == 0 else "issues_found",
                "error_count": error_count,
                "output_file": str(output_file),
                "return_code": result.returncode
            }
            
            logger.info(f"Mypy analysis completed: {error_count} type errors found")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to run mypy analysis: {e}")
            return {
                "tool": "mypy",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_dependency_graph_analysis(self):
        """Generate and analyze dependency graph"""
        logger.info("Generating dependency graph...")
        
        try:
            # Install pydeps if not already installed
            pip_path = self.get_venv_pip()
            subprocess.run([pip_path, "install", "pydeps"], capture_output=True, check=True)
            
            # Generate dependency graph for each service
            python_path = self.get_venv_python()
            graphs = {}
            
            for service_dir in ["user_service", "post_service", "messaging_service", 
                               "group_service", "ai_sandbox_service"]:
                service_path = self.project_root / "src" / service_dir
                if service_path.exists():
                    output_file = self.analysis_dir / f"{service_dir}_dependencies.svg"
                    
                    cmd = [
                        python_path, "-m", "pydeps",
                        str(service_path),
                        "--noshow",
                        "--max-bacon", "10",
                        "--cluster",
                        "--output", str(output_file)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0 and output_file.exists():
                        graphs[service_dir] = str(output_file)
            
            # Generate summary
            summary = {
                "tool": "pydeps",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success" if graphs else "warning",
                "generated_graphs": graphs,
                "graph_count": len(graphs)
            }
            
            logger.info(f"Dependency graph analysis completed: {len(graphs)} graphs generated")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate dependency graph: {e}")
            return {
                "tool": "pydeps",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_analysis(self):
        """Run all static code analysis tools"""
        logger.info("Starting comprehensive static code analysis...")
        
        try:
            # Run all analysis tools in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self.run_flake8_analysis): "flake8",
                    executor.submit(self.run_bandit_analysis): "bandit",
                    executor.submit(self.run_safety_check): "safety",
                    executor.submit(self.run_pylint_analysis): "pylint",
                    executor.submit(self.run_radon_analysis): "radon",
                    executor.submit(self.run_mypy_analysis): "mypy",
                    executor.submit(self.run_dependency_graph_analysis): "dependency_graph"
                }
                
                results = {}
                for future in concurrent.futures.as_completed(futures):
                    tool_name = futures[future]
                    try:
                        results[tool_name] = future.result()
                    except Exception as e:
                        logger.error(f"Error running {tool_name}: {e}")
                        results[tool_name] = {
                            "tool": tool_name,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "status": "error",
                            "error": str(e)
                        }
            
            # Generate overall summary
            success_count = sum(1 for tool, result in results.items() 
                              if result.get("status") == "success")
            issue_count = sum(1 for tool, result in results.items() 
                            if result.get("status") in ["issues_found", "vulnerabilities_found"])
            error_count = sum(1 for tool, result in results.items() 
                            if result.get("status") == "error")
            
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "tools_run": len(results),
                "success_count": success_count,
                "issue_count": issue_count,
                "error_count": error_count,
                "overall_status": "success" if error_count == 0 and issue_count == 0 else "issues_found",
                "results": results
            }
            
            # Save summary to file
            with open(self.analysis_summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            # Generate human-readable report
            self.generate_report(summary)
            
            logger.info(f"Static code analysis completed: {success_count} successful, "
                       f"{issue_count} with issues, {error_count} with errors")
            return summary
            
        except Exception as e:
            logger.error(f"Static code analysis failed: {e}")
            raise

    def generate_report(self, summary):
        """Generate a human-readable report from the analysis results"""
        logger.info("Generating static analysis report...")
        
        report_file = self.analysis_dir / "static_analysis_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Static Code Analysis Report\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")
            
            # Overall summary
            f.write("## Overall Summary\n\n")
            f.write(f"- **Status**: {summary['overall_status']}\n")
            f.write(f"- **Tools Run**: {summary['tools_run']}\n")
            f.write(f"- **Success Count**: {summary['success_count']}\n")
            f.write(f"- **Issue Count**: {summary['issue_count']}\n")
            f.write(f"- **Error Count**: {summary['error_count']}\n\n")
            
            # Tool-specific results
            for tool_name, result in summary["results"].items():
                f.write(f"## {tool_name.replace('_', ' ').title()}\n\n")
                f.write(f"- **Status**: {result.get('status', 'unknown')}\n")
                
                if tool_name == "flake8":
                    f.write(f"- **Error Count**: {result.get('error_count', 'N/A')}\n")
                    f.write(f"- **Warning Count**: {result.get('warning_count', 'N/A')}\n")
                    f.write(f"- **Output File**: `{result.get('output_file', 'N/A')}`\n\n")
                
                elif tool_name == "bandit":
                    f.write(f"- **High Severity Issues**: {result.get('high_severity_issues', 'N/A')}\n")
                    f.write(f"- **Medium Severity Issues**: {result.get('medium_severity_issues', 'N/A')}\n")
                    f.write(f"- **Low Severity Issues**: {result.get('low_severity_issues', 'N/A')}\n")
                    f.write(f"- **Total Issues**: {result.get('total_issues', 'N/A')}\n")
                    f.write(f"- **Output File**: `{result.get('output_file', 'N/A')}`\n\n")
                
                elif tool_name == "safety":
                    f.write(f"- **Vulnerability Count**: {result.get('vulnerability_count', 'N/A')}\n")
                    f.write(f"- **Requirements Files Checked**: {len(result.get('requirements_files_checked', []))}\n")
                    f.write(f"- **Output File**: `{result.get('output_file', 'N/A')}`\n\n")
                
                elif tool_name == "pylint":
                    score = result.get('score', 'N/A')
                    f.write(f"- **Score**: {score}/10.0\n" if score != 'N/A' else f"- **Score**: {score}\n")
                    f.write(f"- **Output File**: `{result.get('output_file', 'N/A')}`\n\n")
                
                elif tool_name == "radon":
                    complexity = result.get('complexity_distribution', {})
                    f.write(f"- **Total Functions**: {result.get('total_functions', 'N/A')}\n")
                    f.write(f"- **Complexity Distribution**:\n")
                    f.write(f"  - A (Simple): {complexity.get('A', 'N/A')}\n")
                    f.write(f"  - B (Slightly complex): {complexity.get('B', 'N/A')}\n")
                    f.write(f"  - C (Complex): {complexity.get('C', 'N/A')}\n")
                    f.write(f"  - D (More complex): {complexity.get('D', 'N/A')}\n")
                    f.write(f"  - E (Very complex): {complexity.get('E', 'N/A')}\n")
                    f.write(f"  - F (Extremely complex): {complexity.get('F', 'N/A')}\n")
                    f.write(f"- **High Complexity Percentage**: {result.get('high_complexity_percentage', 'N/A')}%\n\n")
                
                elif tool_name == "mypy":
                    f.write(f"- **Error Count**: {result.get('error_count', 'N/A')}\n")
                    f.write(f"- **Output File**: `{result.get('output_file', 'N/A')}`\n\n")
                
                elif tool_name == "dependency_graph":
                    f.write(f"- **Graph Count**: {result.get('graph_count', 'N/A')}\n")
                    if "generated_graphs" in result:
                        f.write("- **Generated Graphs**:\n")
                        for service, graph_file in result["generated_graphs"].items():
                            f.write(f"  - {service}: `{graph_file}`\n")
                    f.write("\n")
                
                if result.get("status") == "error" and "error" in result:
                    f.write(f"- **Error**: {result['error']}\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            # Flake8 recommendations
            flake8_result = summary["results"].get("flake8", {})
            if flake8_result.get("error_count", 0) > 0 or flake8_result.get("warning_count", 0) > 0:
                f.write("### Code Quality (Flake8)\n")
                f.write("- Address PEP 8 style issues and syntax errors identified by Flake8\n")
                f.write("- Focus on fixing errors before warnings\n")
                f.write(f"- See detailed report in `{flake8_result.get('output_file', 'N/A')}`\n\n")
            
            # Bandit recommendations
            bandit_result = summary["results"].get("bandit", {})
            if bandit_result.get("total_issues", 0) > 0:
                f.write("### Security (Bandit)\n")
                f.write("- Address high severity security issues immediately\n")
                f.write("- Review and fix medium severity issues\n")
                f.write("- Document any low severity issues that cannot be fixed\n")
                f.write(f"- See detailed report in `{bandit_result.get('output_file', 'N/A')}`\n\n")
            
            # Safety recommendations
            safety_result = summary["results"].get("safety", {})
            if safety_result.get("vulnerability_count", 0) > 0:
                f.write("### Dependencies (Safety)\n")
                f.write("- Update vulnerable dependencies to secure versions\n")
                f.write("- Consider alternative packages if updates are not available\n")
                f.write(f"- See detailed report in `{safety_result.get('output_file', 'N/A')}`\n\n")
            
            # Pylint recommendations
            pylint_result = summary["results"].get("pylint", {})
            pylint_score = pylint_result.get("score")
            if pylint_score is not None and pylint_score < 7:
                f.write("### Code Quality (Pylint)\n")
                f.write("- Improve code quality to achieve a Pylint score of at least 7.0/10.0\n")
                f.write("- Focus on fixing issues related to maintainability and readability\n")
                f.write(f"- See detailed report in `{pylint_result.get('output_file', 'N/A')}`\n\n")
            elif pylint_score is None:
                f.write("### Code Quality (Pylint)\n")
                f.write("- Pylint analysis did not produce a score, review the output file for details\n")
                f.write("- Address any issues preventing proper code analysis\n")
                f.write(f"- See detailed report in `{pylint_result.get('output_file', 'N/A')}`\n\n")
            
            # Radon recommendations
            radon_result = summary["results"].get("radon", {})
            if radon_result.get("high_complexity_percentage", 0) > 10:
                f.write("### Code Complexity (Radon)\n")
                f.write("- Refactor complex functions (categories E and F) to reduce complexity\n")
                f.write("- Break down large functions into smaller, more manageable pieces\n")
                f.write("- Aim to have less than 10% of functions in high complexity categories\n\n")
            
            # Mypy recommendations
            mypy_result = summary["results"].get("mypy", {})
            if mypy_result.get("error_count", 0) > 0:
                f.write("### Type Checking (Mypy)\n")
                f.write("- Add type annotations to improve code reliability\n")
                f.write("- Fix type errors identified by Mypy\n")
                f.write(f"- See detailed report in `{mypy_result.get('output_file', 'N/A')}`\n\n")
        
        logger.info(f"Static analysis report generated: {report_file}")
        return report_file

if __name__ == "__main__":
    analyzer = StaticCodeAnalysis()
    analyzer.run_analysis()
