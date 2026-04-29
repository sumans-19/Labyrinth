# 🛡️ Labyrinth Forge - Firewall Fix Script

Write-Host "Checking Network Profile..." -ForegroundColor Cyan
$profile = Get-NetConnectionProfile -InterfaceAlias "Wi-Fi"
Write-Host "Current Profile: $($profile.NetworkCategory)" -ForegroundColor Yellow

if ($profile.NetworkCategory -eq "Public") {
    Write-Host "[!] Network is set to PUBLIC. Firewall will block connections." -ForegroundColor Red
}

Write-Host "`n[*] Opening ports 8000, 3000, and 2222 in Windows Firewall..." -ForegroundColor Cyan

# Remove old rules if they exist to prevent duplicates
Remove-NetFirewallRule -DisplayName "LabyrinthForge-Honeypot" -ErrorAction SilentlyContinue

# Add new rule
New-NetFirewallRule -DisplayName "LabyrinthForge-Honeypot" `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort 8000,5173,2222,8080 `
    -RemoteAddress Any `
    -Profile Any `
    -Description "Allow external connections for Labyrinth Forge system."

Write-Host "[SUCCESS] Firewall rules updated! Your friend should now be able to connect." -ForegroundColor Green
Write-Host "Host IP: $(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi' | Select-Object -ExpandProperty IPAddress)" -ForegroundColor Green
