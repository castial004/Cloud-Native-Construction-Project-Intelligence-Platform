# =============================================================================
# CCPIP - Windows PowerShell launcher
#
#   .\run.ps1          Start everything, run the pipeline, print the URL
#   .\run.ps1 down     Stop and remove containers + data
#   .\run.ps1 logs     Follow the web + pipeline logs
#
# If PowerShell blocks the script, run once:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# =============================================================================

param(
    [string]$Command = "up"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Test-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: Docker is not installed. Install Docker Desktop first:" -ForegroundColor Red
        Write-Host "       https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        exit 1
    }
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker daemon is not running. Start Docker Desktop and retry." -ForegroundColor Red
        exit 1
    }
}

switch ($Command) {
    "down" {
        Write-Host "Stopping CCPIP ..." -ForegroundColor Cyan
        docker compose down -v
        Write-Host "Done." -ForegroundColor Green
    }
    "logs" {
        docker compose logs -f web pipeline
    }
    default {
        Test-Docker

        if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

        $webPort = "8080"
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^WEB_PORT=(.+)$") { $webPort = $Matches[1].Trim() }
        }

        Write-Host "Building image (first run takes a few minutes) ..." -ForegroundColor Cyan
        # Classic builder + host networking avoids Docker Desktop DNS issues.
        docker build --network=host -t platform-app:latest .
        if ($LASTEXITCODE -ne 0) { Write-Host "Build failed." -ForegroundColor Red; exit 1 }

        Write-Host "Starting database, API and web UI ..." -ForegroundColor Cyan
        docker compose up -d db ingestion web

        Write-Host "Waiting for the database ..." -ForegroundColor Cyan
        for ($i = 0; $i -lt 60; $i++) {
            docker compose exec -T db pg_isready -U ccpip > $null 2>&1
            if ($LASTEXITCODE -eq 0) { break }
            Start-Sleep -Seconds 1
        }

        Write-Host "Running the data pipeline (generate -> ingest -> EVM -> train -> score) ..." -ForegroundColor Cyan
        docker compose up -d pipeline

        for ($i = 0; $i -lt 300; $i++) {
            $cid = (docker compose ps -aq pipeline)
            if ($cid) {
                $state = (docker inspect -f "{{.State.Status}}" $cid)
                if ($state -eq "exited") { break }
            }
            Start-Sleep -Seconds 2
        }

        Write-Host ""
        Write-Host "===================================================================" -ForegroundColor Green
        Write-Host "  CCPIP is running. Open the dashboard:" -ForegroundColor Green
        Write-Host ""
        Write-Host "      http://localhost:$webPort" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Stop:  .\run.ps1 down"
        Write-Host "  Logs:  .\run.ps1 logs"
        Write-Host "===================================================================" -ForegroundColor Green
    }
}
