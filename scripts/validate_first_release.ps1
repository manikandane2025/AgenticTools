$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Invoke-RequiredStep {
    param(
        [string]$Name,
        [string]$Command
    )

    Write-Host "==> $Name"
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name"
    }
}

Invoke-RequiredStep "Cleanup" "Remove-Item -Recurse -Force build, dist, .pytest_cache, .mypy_cache, .ruff_cache, htmlcov -ErrorAction SilentlyContinue"
Invoke-RequiredStep "Format Check" "python -m ruff format --check src tests scripts"
Invoke-RequiredStep "Lint" "python -m ruff check src tests scripts"
Invoke-RequiredStep "Type Check" "python -m mypy src"
Invoke-RequiredStep "Tests" "python -m pytest -q"
Invoke-RequiredStep "Branch Coverage" "python -m pytest --cov=src/paccaassure_common_tools --cov-branch --cov-report=xml -q"
Invoke-RequiredStep "Source Scans And Reports" "python scripts\generate_first_release_code_quality.py"
Invoke-RequiredStep "Package Build" "python -m build"
Invoke-RequiredStep "Package Inspection" "python -m pytest tests\integration\test_package_content.py -q"
Invoke-RequiredStep "Clean Install Smoke" "docker run --rm -v ${repoRoot}:/workspace python:3.12-slim bash -lc `"cd /workspace && python -m pip install --upgrade pip && python -m pip install dist/paccaassure_common_tools-*-py3-none-any.whl && python -c 'import paccaassure_common_tools'`""
Invoke-RequiredStep "Vulnerability Audit" "python -m pip_audit -r requirements.lock -f json -o artifacts\reports\vulnerability-report.json"
Invoke-RequiredStep "License Compliance" "python scripts\generate_release_closure.py"
Invoke-RequiredStep "SBOM" "cyclonedx-py requirements requirements.lock --output-file artifacts\reports\sbom.json"
Invoke-RequiredStep "Docker Build" "docker build -t pacca-tools-core:0.1.0 ."
Invoke-RequiredStep "Docker Security And Certification" "python scripts\generate_cross_cutting_hardening.py"
Invoke-RequiredStep "Release Consistency" "python scripts\generate_first_release_code_quality.py"
