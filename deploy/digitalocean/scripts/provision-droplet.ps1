# PowerShell wrapper: provision DigitalOcean droplet (requires doctl + token).
# Usage:
#   $env:DIGITALOCEAN_ACCESS_TOKEN = "dop_v1_..."
#   $env:DO_SSH_KEY_FINGERPRINT = "xx:xx:..."
#   .\deploy\digitalocean\scripts\provision-droplet.ps1

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$bashScript = Join-Path $here "provision-droplet.sh"

if (-not $env:DIGITALOCEAN_ACCESS_TOKEN) {
  throw "Set DIGITALOCEAN_ACCESS_TOKEN first"
}
if (-not $env:DO_SSH_KEY_FINGERPRINT) {
  Write-Host "List SSH keys with: doctl compute ssh-key list"
  throw "Set DO_SSH_KEY_FINGERPRINT first"
}

if (-not (Get-Command doctl -ErrorAction SilentlyContinue)) {
  Write-Host "doctl not found. Install: https://docs.digitalocean.com/reference/doctl/how-to/install/"
  Write-Host "Or: winget install DigitalOcean.Doctl"
  throw "doctl required"
}

if (Get-Command bash -ErrorAction SilentlyContinue) {
  bash $bashScript
} elseif (Get-Command wsl -ErrorAction SilentlyContinue) {
  wsl -e bash $bashScript
} else {
  throw "Need bash or WSL to run provision-droplet.sh"
}
