# Run in an elevated PowerShell on SERVER. Idempotent.
# 1) OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
# key-based login for administrators: append your public key to this file (one line), then fix ACLs
$auth = "$env:ProgramData\ssh\administrators_authorized_keys"
if (-not (Test-Path $auth)) { New-Item -ItemType File -Path $auth | Out-Null }
icacls $auth /inheritance:r /grant "Administrators:F" /grant "SYSTEM:F" | Out-Null
Write-Host "Append the Mac's public key to $auth"

# 2) Firewall: 22 and 443 only from the Tailscale range; 53 for the CoreDNS container; block from LAN
$ts = "100.64.0.0/10"
foreach ($p in 22,443,53) {
  Remove-NetFirewallRule -DisplayName "AGL allow $p from Tailscale" -ErrorAction SilentlyContinue
  New-NetFirewallRule -DisplayName "AGL allow $p from Tailscale" -Direction Inbound -Protocol TCP -LocalPort $p -RemoteAddress $ts -Action Allow | Out-Null
  Remove-NetFirewallRule -DisplayName "AGL block $p elsewhere" -ErrorAction SilentlyContinue
  New-NetFirewallRule -DisplayName "AGL block $p elsewhere" -Direction Inbound -Protocol TCP -LocalPort $p -Action Block | Out-Null
}
Remove-NetFirewallRule -DisplayName "AGL allow 53 udp from Tailscale" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "AGL allow 53 udp from Tailscale" -Direction Inbound -Protocol UDP -LocalPort 53 -RemoteAddress $ts -Action Allow | Out-Null
# Windows rule precedence: Block beats Allow for the same traffic, so the Allow rules above only matter
# where the Block rule does not apply. Make the Block rules LAN-scoped instead of global:
foreach ($p in 22,443,53) { Set-NetFirewallRule -DisplayName "AGL block $p elsewhere" -RemoteAddress "LocalSubnet","Internet" }
Write-Host "Firewall: 22/443/53 allowed from $ts only."
Write-Host "Reminder: nothing is forwarded on the home router; Docker Desktop 'Expose daemon on tcp://localhost:2375' must stay OFF."
