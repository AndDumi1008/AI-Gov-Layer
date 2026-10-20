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

# 2) Firewall. Windows Firewall's inbound default is Block, so we only need Allow rules scoped to the Tailscale
#    range. Do NOT add Block rules: Block always wins over Allow, and Windows classifies Tailscale peers as
#    "Internet" (they are not on the local subnet), so a Block-from-Internet rule would also block the tailnet.
$ts = "100.64.0.0/10"
Get-NetFirewallRule -DisplayName "AGL block *" -ErrorAction SilentlyContinue | Remove-NetFirewallRule   # from an earlier version of this script
foreach ($p in 22,53,4000,8443) {   # 4000 = gateway plain HTTP on the tailnet, 8443 = Caddy TLS (443 is tailscaled's)
  Remove-NetFirewallRule -DisplayName "AGL allow $p from Tailscale" -ErrorAction SilentlyContinue
  New-NetFirewallRule -DisplayName "AGL allow $p from Tailscale" -Direction Inbound -Protocol TCP -LocalPort $p -RemoteAddress $ts -Action Allow -Profile Any | Out-Null
}
Remove-NetFirewallRule -DisplayName "AGL allow 53 udp from Tailscale" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "AGL allow 53 udp from Tailscale" -Direction Inbound -Protocol UDP -LocalPort 53 -RemoteAddress $ts -Action Allow -Profile Any | Out-Null
# The OpenSSH feature installs its own rule "OpenSSH SSH Server (sshd)" allowing 22 from ANY address. Scope it to the tailnet.
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue | Set-NetFirewallRule -RemoteAddress $ts -Profile Any
Write-Host "Firewall: 22/53/4000/8443 allowed from $ts only (no broad rules for these ports)."
Write-Host "Check: Get-Service sshd ; Get-NetFirewallRule -DisplayName 'AGL*','OpenSSH*' | Format-Table DisplayName,Enabled,Action,Profile"
Write-Host "Reminder: nothing is forwarded on the home router; Docker Desktop 'Expose daemon on tcp://localhost:2375' must stay OFF."
