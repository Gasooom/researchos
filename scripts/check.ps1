$ErrorActionPreference = "Stop"

Write-Host "Running tests..."
pytest -q

Write-Host "Checking code..."
ruff check .

Write-Host "Checking formatting..."
ruff format --check .

Write-Host "All checks passed."