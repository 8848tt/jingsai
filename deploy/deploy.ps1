# 一键部署（请在仓库根目录执行：.\deploy\deploy.ps1）
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 docker 命令，请先安装 Docker Desktop。"
}

if (-not (Test-Path ".env")) {
    Copy-Item "deploy\.env.example" ".env"
    Write-Host "已从 deploy\.env.example 创建 .env，建议修改 DJANGO_SECRET_KEY 后重新部署。"
}

docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$port = "8080"
if (Test-Path ".env") {
    $line = Get-Content ".env" | Where-Object { $_ -match '^\s*WEB_PORT\s*=' } | Select-Object -First 1
    if ($line -match '=\s*(\d+)') { $port = $Matches[1] }
}

Write-Host ""
Write-Host "部署完成。浏览器打开: http://localhost:$port"
Write-Host "创建管理员: docker compose exec api python manage.py createsuperuser"
Write-Host "然后在 Django Admin 将用户 role 设为 admin。"
