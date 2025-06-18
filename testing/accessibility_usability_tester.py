#!/usr/bin/env python3
"""
Surgical-Precision Testing - Accessibility and Usability Assessment
This script conducts accessibility and usability assessments for the Future Social (FS) project.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("testing/accessibility_usability_testing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fs_accessibility_usability_testing")

class AccessibilityUsabilityTester:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_env_dir = self.project_root / "testing"
        self.test_results_dir = self.test_env_dir / "results"
        self.mapping_dir = self.test_results_dir / "element_mapping"
        self.accessibility_dir = self.test_results_dir / "accessibility_usability_tests"
        self.accessibility_summary_file = self.accessibility_dir / "accessibility_usability_summary.json"
        
        # Ensure directories exist
        self.accessibility_dir.mkdir(exist_ok=True, parents=True)
        
        # Load API routes and documentation (if available)
        self.api_routes = self._load_json(self.mapping_dir / "api_routes.json")
        self.api_docs_path = self.project_root / "fs_project_documentation.md" # Assuming this exists
        
        logger.info("Accessibility and Usability tester initialized.")

    def _load_json(self, file_path):
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"File not found: {file_path}")
                return []
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []

    def _read_file_content(self, file_path):
        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.warning(f"File not found: {file_path}")
                return ""
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""

    def assess_api_accessibility(self):
        """Assess API design for accessibility considerations."""
        logger.info("Assessing API accessibility...")
        results = {
            "test_name": "API Accessibility Assessment",
            "description": "Evaluates API design for clarity, consistency, and ease of use for developers, including those using assistive technologies.",
            "findings": []
        }

        if not self.api_routes:
            results["findings"].append({
                "severity": "High",
                "issue": "API routes mapping file (api_routes.json) not found or empty.",
                "recommendation": "Ensure API routes are mapped and available for assessment."
            })
            return results

        # Check 1: Consistent Naming Conventions
        path_segments = []
        for route in self.api_routes:
            path_segments.extend(re.findall(r"\w+", route.get("path", "")))
        
        if path_segments:
            # Simple check: are most segments lowercase with underscores (snake_case) or camelCase?
            snake_case_count = sum(1 for s in path_segments if re.match(r"^[a-z_]+[a-z0-9_]*$", s))
            camel_case_count = sum(1 for s in path_segments if re.match(r"^[a-z]+[a-zA-Z0-9]*$", s))
            
            if not (snake_case_count > len(path_segments) * 0.7 or camel_case_count > len(path_segments) * 0.7):
                results["findings"].append({
                    "severity": "Low",
                    "issue": "API path naming conventions appear inconsistent (mix of snake_case, camelCase, or other styles).",
                    "recommendation": "Adopt a consistent naming convention (e.g., snake_case or camelCase) for all API paths and parameters for better readability and predictability."
                })
        else:
             results["findings"].append({
                "severity": "Medium",
                "issue": "No path segments found to analyze for naming conventions.",
                "recommendation": "Ensure API routes are correctly defined in api_routes.json."
            })

        # Check 2: Clear and Descriptive Paths
        ambiguous_paths = [r for r in self.api_routes if len(r.get("path", "").split("/")) < 2 or "generic" in r.get("path", "").lower()]
        if ambiguous_paths:
            results["findings"].append({
                "severity": "Medium",
                "issue": f"{len(ambiguous_paths)} API paths may not be sufficiently descriptive (e.g., too short or generic).",
                "recommendation": "Ensure API paths are clear, descriptive, and reflect the resource hierarchy."
            })

        # Check 3: Standard HTTP Methods
        non_standard_methods = [r for r in self.api_routes if r.get("method", "").upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]]
        if non_standard_methods:
            results["findings"].append({
                "severity": "Medium",
                "issue": f"{len(non_standard_methods)} API routes use non-standard HTTP methods.",
                "recommendation": "Use standard HTTP methods (GET, POST, PUT, DELETE, PATCH) appropriately for CRUD operations."
            })
        
        # Check 4: Consistent Error Handling (Conceptual - based on documentation if available)
        api_docs_content = self._read_file_content(self.api_docs_path)
        if api_docs_content:
            if not re.search(r"Error Handling|Error Responses|Status Codes", api_docs_content, re.IGNORECASE):
                results["findings"].append({
                    "severity": "Medium",
                    "issue": "API documentation does not clearly define standard error handling procedures or common error response formats.",
                    "recommendation": "Document standard error responses (e.g., using RFC 7807 Problem Details) and common status codes consistently across the API."
                })
        else:
            results["findings"].append({
                "severity": "Low",
                "issue": "API documentation file (fs_project_documentation.md) not found. Could not assess documented error handling.",
                "recommendation": "Provide comprehensive API documentation that includes error handling strategies."
            })

        # Check 5: Support for Pagination and Filtering (Conceptual)
        if api_docs_content:
            if not (re.search(r"Pagination", api_docs_content, re.IGNORECASE) and re.search(r"Filtering|Sorting", api_docs_content, re.IGNORECASE)):
                results["findings"].append({
                    "severity": "Low",
                    "issue": "API documentation does not clearly specify support for pagination, filtering, or sorting on list endpoints.",
                    "recommendation": "Implement and document pagination (e.g., limit/offset or cursor-based) and filtering/sorting capabilities for list endpoints to improve usability and performance."
                })
        
        if not results["findings"]:
            results["findings"].append({
                "severity": "Info",
                "issue": "No major API accessibility issues identified based on automated checks.",
                "recommendation": "Continue to follow API design best practices."
            })

        return results

    def assess_api_usability_and_documentation(self):
        """Assess API usability and the quality of its documentation."""
        logger.info("Assessing API usability and documentation...")
        results = {
            "test_name": "API Usability and Documentation Assessment",
            "description": "Evaluates the ease of understanding and using the API, primarily through its documentation.",
            "findings": []
        }

        api_docs_content = self._read_file_content(self.api_docs_path)
        if not api_docs_content:
            results["findings"].append({
                "severity": "High",
                "issue": "API documentation file (fs_project_documentation.md) not found or empty.",
                "recommendation": "Create comprehensive API documentation. This is crucial for usability."
            })
            return results

        # Check 1: Completeness of Documentation
        # - Overview, Authentication, Endpoints, Request/Response examples, Error codes
        required_sections = ["Overview", "Authentication", "API Endpoints", "Request Format", "Response Format", "Error Codes"]
        missing_sections = []
        for section in required_sections:
            if not re.search(fr"(^#{{1,3}}\s*{section}|\*\*{section}\*\*)_?", api_docs_content, re.IGNORECASE | re.MULTILINE):
                missing_sections.append(section)
        
        if missing_sections:
            results["findings"].append({
                "severity": "High",
                "issue": f"API documentation is missing key sections: {', '.join(missing_sections)}.",
                "recommendation": "Ensure API documentation includes all essential sections: Overview, Authentication, detailed Endpoint descriptions with Request/Response examples, and Error Code explanations."
            })

        # Check 2: Clarity of Examples
        if not re.search(r"Example Request|Request Example|Example Response|Response Example", api_docs_content, re.IGNORECASE):
            results["findings"].append({
                "severity": "Medium",
                "issue": "API documentation lacks clear request/response examples for endpoints.",
                "recommendation": "Provide clear, practical examples for each API endpoint, showing sample requests and corresponding responses (including error responses)."
            })
        elif len(re.findall(r"```json", api_docs_content, re.IGNORECASE)) < len(self.api_routes) * 0.5: # Heuristic: at least half endpoints have JSON examples
             results["findings"].append({
                "severity": "Low",
                "issue": "API documentation may not have sufficient request/response examples for all endpoints.",
                "recommendation": "Ensure each API endpoint has clear request and response examples, including different scenarios (success, error)."
            })

        # Check 3: Readability and Structure
        # - Use of Markdown, headings, code blocks
        if len(re.findall(r"^#+\s+", api_docs_content, re.MULTILINE)) < 5: # Heuristic for structure
            results["findings"].append({
                "severity": "Low",
                "issue": "API documentation may lack proper structure and formatting (e.g., insufficient use of headings).",
                "recommendation": "Structure API documentation logically using Markdown headings, subheadings, lists, and code blocks for readability."
            })

        # Check 4: Versioning Information
        if not re.search(r"API Versioning|Version Information", api_docs_content, re.IGNORECASE):
            results["findings"].append({
                "severity": "Medium",
                "issue": "API documentation does not provide information on API versioning strategy.",
                "recommendation": "Clearly document the API versioning strategy (e.g., URI versioning, header versioning) and how to use different versions."
            })
        
        # Check 5: Rate Limiting Information
        if not re.search(r"Rate Limiting|API Limits", api_docs_content, re.IGNORECASE):
            results["findings"].append({
                "severity": "Low",
                "issue": "API documentation does not provide information on rate limiting.",
                "recommendation": "Document any rate limits imposed on the API to help developers manage their usage."
            })

        if not results["findings"]:
            results["findings"].append({
                "severity": "Info",
                "issue": "No major API usability or documentation issues identified based on automated checks.",
                "recommendation": "Continue to maintain and improve API documentation."
            })
        
        return results

    def generate_accessibility_usability_report(self, all_results):
        """Generate a comprehensive accessibility and usability testing report"""
        logger.info("Generating accessibility and usability testing report...")
        
        report_file = self.accessibility_dir / "accessibility_usability_report.md"
        
        with open(report_file, "w") as f:
            f.write("# Accessibility and Usability Assessment Report\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            
            total_findings = 0
            severity_counts = {"High": 0, "Medium": 0, "Low": 0, "Info": 0}
            for test_type, results_list in all_results.items():
                for finding in results_list.get("findings", []):
                    severity = finding.get("severity", "Low")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    total_findings +=1
            
            f.write(f"This assessment identified a total of **{total_findings - severity_counts['Info']} actionable findings** (excluding informational items) related to API accessibility and usability:\n\n")
            f.write(f"- **{severity_counts['High']} High** severity findings\n")
            f.write(f"- **{severity_counts['Medium']} Medium** severity findings\n")
            f.write(f"- **{severity_counts['Low']} Low** severity findings\n\n")
            f.write("Note: Since this is a backend-focused project, accessibility and usability primarily relate to API design and documentation from a developer perspective.\n\n")
            
            # Detailed Findings
            f.write("## Detailed Findings\n\n")
            
            for test_type, results_data in all_results.items():
                f.write(f"### {results_data['test_name']}\n\n")
                f.write(f"{results_data['description']}\n\n")
                
                if results_data["findings"]:
                    for finding in results_data["findings"]:
                        if finding['severity'] != "Info": # Don't list Info items as problems
                            f.write(f"- **{finding['severity']}**: {finding['issue']}\n")
                            f.write(f"  - **Recommendation**: {finding['recommendation']}\n\n")
                else:
                    f.write("No specific findings for this test.\n\n")
            
            # Recommendations Summary
            f.write("## Recommendations Summary\n\n")
            f.write("Based on the findings, the following key recommendations are made to improve API accessibility and usability:\n\n")
            
            recommendation_list = []
            for test_type, results_list in all_results.items():
                 for finding in results_list.get("findings", []):
                    if finding["severity"] != "Info":
                        recommendation_list.append(f"**({finding['severity']})** {finding['recommendation']}")
            
            if recommendation_list:
                for i, rec in enumerate(recommendation_list, 1):
                    f.write(f"{i}. {rec}\n")
            else:
                f.write("No specific actionable recommendations based on automated checks. Continue to follow best practices.\n")
            f.write("\n")
            
            # Conclusion
            f.write("## Conclusion\n\n")
            if total_findings - severity_counts['Info'] == 0:
                f.write("The automated accessibility and usability assessment found no major issues in the API design and documentation. Continuous attention to these aspects is recommended as the API evolves.\n\n")
            else:
                f.write(f"The assessment identified areas for improvement in API accessibility and usability, primarily concerning API design consistency and documentation completeness. Addressing these findings will enhance the developer experience and ensure the API is easier to understand and integrate.\n\n")
            f.write("Manual review and testing by developers, including those with disabilities, can provide further insights beyond these automated checks.\n")

        logger.info(f"Accessibility and Usability testing report generated: {report_file}")
        return str(report_file)

    def run_accessibility_usability_tests(self):
        """Run all accessibility and usability tests"""
        logger.info("Starting accessibility and usability assessments...")
        
        try:
            api_accessibility_results = self.assess_api_accessibility()
            api_usability_results = self.assess_api_usability_and_documentation()
            
            all_results = {
                "api_accessibility": api_accessibility_results,
                "api_usability_and_documentation": api_usability_results
            }
            
            report_file = self.generate_accessibility_usability_report(all_results)
            
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "api_accessibility_findings": len(api_accessibility_results.get("findings", [])),
                "api_usability_findings": len(api_usability_results.get("findings", [])),
                "report_file": str(report_file)
            }
            
            with open(self.accessibility_summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            
            logger.info("Accessibility and usability assessments completed")
            return summary
            
        except Exception as e:
            logger.error(f"Accessibility and usability testing failed: {e}")
            raise

if __name__ == "__main__":
    tester = AccessibilityUsabilityTester()
    tester.run_accessibility_usability_tests()
