param([int]$Port = 4173)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
Write-Host "Stormwater running at http://localhost:$Port"
python -m http.server $Port

