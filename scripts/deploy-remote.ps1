# Copy sql/ and docker-compose.yml to a remote VPS
# Usage: .\scripts\deploy-remote.ps1 -Server root@your-host

param(
    [Parameter(Mandatory = $true)]
    [string]$Server,
    [string]$RemoteDir = "/opt/etl-tg-booster"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

ssh $Server "mkdir -p $RemoteDir/sql"
scp -r "$root\sql" "${Server}:${RemoteDir}/"
scp "$root\docker-compose.yml" "${Server}:${RemoteDir}/"

Write-Host "Copied to $Server:$RemoteDir"
Write-Host "Next on server: create .env, then docker compose up -d"
