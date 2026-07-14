$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ("etl_{0:yyyyMMdd}.log" -f (Get-Date))

function Write-Log($message) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message
    Add-Content -Path $logFile -Value $line
    Write-Output $line
}

Write-Log "Starting incremental ETL"
& (Join-Path $root ".venv\Scripts\python.exe") -m etl run --incremental 2>&1 | Out-File -Append $logFile
Write-Log "Finished with exit code $LASTEXITCODE"
