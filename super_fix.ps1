# 🚀 LABYRINTH FORGE - SUPER FIX SCRIPT (Run as Admin)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "═══ STARTING NETWORK & FIREWALL REPAIR ═══" -ForegroundColor Cyan

# 1. Set Network to Private (This is the most important fix)
Write-Host "[*] Setting Wi-Fi profile to 'Private'..." -ForegroundColor Yellow
Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private
if ($?) {
    Write-Host "[SUCCESS] Network set to Private!" -ForegroundColor Green
} else {
    Write-Host "[!] Failed to set Private profile. Manual change may be needed." -ForegroundColor Red
}

# 2. Open Firewall Ports
Write-Host "[*] Opening Firewall Ports (3000, 8000, 2222)..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "Labyrinth-Forge-System"
New-NetFirewallRule -DisplayName "Labyrinth-Forge-System" `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort 3000, 8000, 2222 `
    -Description "Allow Labyrinth Forge traffic"

Write-Host "[SUCCESS] Firewall ports are now OPEN." -ForegroundColor Green

# 3. Final Diagnostic
$hostIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi').IPAddress[0]
Write-Host "`n═══ CONFIGURED AND READY ═══" -ForegroundColor Cyan
Write-Host "Host IP: $hostIp" -ForegroundColor Green
Write-Host "1. Restart Backend and Frontend on YOUR laptop."
Write-Host "2. Have your friend run this in their terminal to test: " -NoNewline
Write-Host "Test-NetConnection -ComputerName $hostIp -Port 8000" -ForegroundColor Yellow
Write-Host "If 'TcpTestSucceeded' is True, everything is perfect!"
