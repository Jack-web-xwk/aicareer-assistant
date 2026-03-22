# UTF-8 BOM - improves Chinese display in Windows PowerShell 5.1
<#
.SYNOPSIS
  AI Career Assistant - local dev launcher (menu / one-shot)

.EXAMPLE
  .\start-services.ps1
  .\start-services.ps1 -Mode all
#>

param(
    [ValidateSet("interactive", "all", "frontend", "backend")]
    [string]$Mode = "interactive"
)

$ErrorActionPreference = "Stop"

# Works whether this file lives in repo root or in scripts\
if (Test-Path (Join-Path $PSScriptRoot "frontend")) {
    $ProjectRoot = Resolve-Path $PSScriptRoot
}
elseif (Test-Path (Join-Path (Join-Path $PSScriptRoot "..") "frontend")) {
    $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
}
else {
    throw "Cannot find project root (no frontend folder next to or above this script)."
}

$FrontendDir = Join-Path $ProjectRoot "frontend"
$BackendDir = Join-Path $ProjectRoot "backend"
$BackendPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Show-Banner {
    Write-Host ""
    Write-Host "  +------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |     AI Career Assistant - Local dev console          |" -ForegroundColor Cyan
    Write-Host "  +------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Project root: " -NoNewline -ForegroundColor DarkGray
    Write-Host $ProjectRoot -ForegroundColor Gray
    Write-Host ""
}

function Show-Menu {
    Write-Host "  --------------- Choose (type number + Enter) ---------------" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "    [1]  " -NoNewline -ForegroundColor Yellow
    Write-Host "Start frontend" -NoNewline
    Write-Host "  -> npm run dev (Vite, http://localhost:5173)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    [2]  " -NoNewline -ForegroundColor Yellow
    Write-Host "Start backend" -NoNewline
    Write-Host "  -> python main.py (FastAPI, http://localhost:8000)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    [3]  " -NoNewline -ForegroundColor Yellow
    Write-Host "Start both" -NoNewline
    Write-Host "  -> two new windows: backend then frontend" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    [h]  Help" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    [0]  Exit" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  ------------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-HelpText {
    Write-Host ""
    Write-Host "  - Services run in NEW PowerShell windows; close window to stop." -ForegroundColor Gray
    Write-Host "  - Backend needs venv: " -NoNewline -ForegroundColor Gray
    Write-Host "backend\.venv" -ForegroundColor Yellow
    Write-Host "  - Frontend: first run (in frontend folder): " -NoNewline -ForegroundColor Gray
    Write-Host 'npm install' -ForegroundColor Yellow
    Write-Host "  - API docs: " -NoNewline -ForegroundColor Gray
    Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
}

function Start-Frontend {
    if (-not (Test-Path $FrontendDir)) {
        throw "frontend folder not found: $FrontendDir"
    }

    Write-Host "  -> Starting frontend (new window)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$FrontendDir'; Write-Host '[frontend] Vite' -ForegroundColor Cyan; npm run dev"
    ) | Out-Null
    Write-Host "  [OK] Frontend command sent. Open http://localhost:5173 if needed." -ForegroundColor DarkGreen
}

function Start-Backend {
    if (-not (Test-Path $BackendDir)) {
        throw "backend folder not found: $BackendDir"
    }
    if (-not (Test-Path $BackendPython)) {
        throw "venv python not found: $BackendPython (create backend\.venv first)"
    }

    Write-Host "  -> Starting backend (new window)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$BackendDir'; Write-Host '[backend] FastAPI' -ForegroundColor Cyan; & '$BackendPython' main.py"
    ) | Out-Null
    Write-Host "  [OK] Backend command sent. API http://localhost:8000 | docs http://localhost:8000/docs" -ForegroundColor DarkGreen
}

function Invoke-InteractiveLoop {
    Show-Banner
    Write-Host "  Interactive mode: enter 1/2/3, 0 to exit." -ForegroundColor DarkGray
    Show-HelpText

    while ($true) {
        Show-Menu
        $raw = Read-Host "  Your choice"
        $choice = if ($null -eq $raw) { "" } else { $raw.Trim().ToLower() }

        try {
            switch ($choice) {
                "1" { Start-Frontend }
                "2" { Start-Backend }
                "3" {
                    Write-Host "  Starting backend, then frontend..." -ForegroundColor DarkGray
                    Start-Backend
                    Start-Sleep -Milliseconds 400
                    Start-Frontend
                    Write-Host "  [OK] Both start commands sent." -ForegroundColor DarkGreen
                }
                "0" {
                    Write-Host ""
                    Write-Host "  Bye." -ForegroundColor Cyan
                    Write-Host ""
                    exit 0
                }
                "q" {
                    Write-Host ""
                    Write-Host "  Bye." -ForegroundColor Cyan
                    Write-Host ""
                    exit 0
                }
                "h" { Show-HelpText }
                "" {
                    Write-Host "  (empty input) Type 1, 2, 3, h, or 0." -ForegroundColor Yellow
                }
                default {
                    Write-Host "  Unknown: $choice . Use 1 / 2 / 3 / h / 0." -ForegroundColor Yellow
                }
            }
        }
        catch {
            Write-Host "  [ERR] $_" -ForegroundColor Red
        }

        Write-Host ""
        Write-Host "  ------------------------------------------------------------" -ForegroundColor DarkGray
        $null = Read-Host "  Press Enter to return to menu"
        Write-Host ""
    }
}

if ($Mode -ne "interactive") {
    Show-Banner
    switch ($Mode) {
        "frontend" { Start-Frontend }
        "backend"  { Start-Backend }
        "all" {
            Start-Backend
            Start-Sleep -Milliseconds 400
            Start-Frontend
            Write-Host "  [OK] Sent all: backend + frontend" -ForegroundColor DarkGreen
        }
    }
    Write-Host ""
    exit 0
}

Invoke-InteractiveLoop
