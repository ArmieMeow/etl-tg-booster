# Копирование sql/ и docker-compose.yml на удалённый VPS
# Пример: .\scripts\deploy-remote.ps1 -Server root@your-host

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

Write-Host "Скопировано в $Server:$RemoteDir"
Write-Host "На сервере: создайте .env, затем docker compose up -d"
