# Static Code Analysis Report

Generated: 2025-06-17T20:12:37.985345

## Overall Summary

- **Status**: issues_found
- **Tools Run**: 7
- **Success Count**: 3
- **Issue Count**: 3
- **Error Count**: 0

## Bandit

- **Status**: issues_found
- **High Severity Issues**: 5
- **Medium Severity Issues**: 0
- **Low Severity Issues**: 0
- **Total Issues**: 5
- **Output File**: `/home/ubuntu/fs_project/testing/results/static_analysis/bandit_results.json`

## Flake8

- **Status**: issues_found
- **Error Count**: 136
- **Warning Count**: 76
- **Output File**: `/home/ubuntu/fs_project/testing/results/static_analysis/flake8_results.txt`

## Radon

- **Status**: success
- **Total Functions**: 0
- **Complexity Distribution**:
  - A (Simple): 0
  - B (Slightly complex): 0
  - C (Complex): 0
  - D (More complex): 0
  - E (Very complex): 0
  - F (Extremely complex): 0
- **High Complexity Percentage**: 0%

## Mypy

- **Status**: issues_found
- **Error Count**: 1
- **Output File**: `/home/ubuntu/fs_project/testing/results/static_analysis/mypy_results.txt`

## Dependency Graph

- **Status**: warning
- **Graph Count**: 0
- **Generated Graphs**:

## Safety

- **Status**: success
- **Vulnerability Count**: 0
- **Requirements Files Checked**: 5
- **Output File**: `/home/ubuntu/fs_project/testing/results/static_analysis/safety_results.json`

## Pylint

- **Status**: success
- **Score**: None/10.0
- **Output File**: `/home/ubuntu/fs_project/testing/results/static_analysis/pylint_results.txt`

## Recommendations

### Code Quality (Flake8)
- Address PEP 8 style issues and syntax errors identified by Flake8
- Focus on fixing errors before warnings
- See detailed report in `/home/ubuntu/fs_project/testing/results/static_analysis/flake8_results.txt`

### Security (Bandit)
- Address high severity security issues immediately
- Review and fix medium severity issues
- Document any low severity issues that cannot be fixed
- See detailed report in `/home/ubuntu/fs_project/testing/results/static_analysis/bandit_results.json`

### Code Quality (Pylint)
- Pylint analysis did not produce a score, review the output file for details
- Address any issues preventing proper code analysis
- See detailed report in `/home/ubuntu/fs_project/testing/results/static_analysis/pylint_results.txt`

### Type Checking (Mypy)
- Add type annotations to improve code reliability
- Fix type errors identified by Mypy
- See detailed report in `/home/ubuntu/fs_project/testing/results/static_analysis/mypy_results.txt`

