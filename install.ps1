# 一鍵安裝道樞到目標專案（Windows）
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File install.ps1 [目標目錄]
#
# 安裝內容：skills\daozhu + mcp\* 到 <目標>\.claude\
param([string]$Target = ".")

$ErrorActionPreference = "Stop"
$Src = $PSScriptRoot
$dest = Join-Path $Target ".claude"

Write-Host "安裝道樞 → $dest"

New-Item -ItemType Directory -Force -Path (Join-Path $dest "skills") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dest "daozhu-mcp\tests") | Out-Null

Copy-Item -Recurse -Force (Join-Path $Src "skills\daozhu") (Join-Path $dest "skills\")
Copy-Item -Force (Join-Path $Src "mcp\*.py") (Join-Path $dest "daozhu-mcp\")
Copy-Item -Force (Join-Path $Src "mcp\requirements.txt"), (Join-Path $Src "mcp\config.yaml.example") (Join-Path $dest "daozhu-mcp\")
Copy-Item -Force (Join-Path $Src "mcp\tests\*.py") (Join-Path $dest "daozhu-mcp\tests\")

Write-Host ""
Write-Host "✓ 道樞已安裝。接著三步即可啟用："
Write-Host "  1) pip install -r $dest\daozhu-mcp\requirements.txt"
Write-Host "  2) 依 .mcp.json.example 建立專案根 .mcp.json（含 daozhu server）"
Write-Host "  3) .claude\settings.local.json 加 {""enableAllProjectMcpServers"": true}"
Write-Host "  4) Reload Window，/mcp 確認 daozhu Connected"
