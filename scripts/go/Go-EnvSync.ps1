# Encrypted .env sync — .env.enc is committed; .env stays gitignored.
# Both machines share a passphrase via .env.key (gitignored, set up once per machine).
#
# Encrypt:  Protect-PolySaaSEnv   -RepoRoot $scriptDir   (before commit)
# Decrypt:  Unprotect-PolySaaSEnv -RepoRoot $scriptDir   (after pull)

function _Get-EnvAesKey {
    param([string]$RepoRoot)

    $keyFile = Join-Path $RepoRoot ".env.key"
    if (-not (Test-Path $keyFile)) {
        Write-Host "  .env.key not found. Create it once on this machine:" -ForegroundColor Red
        Write-Host "  Set-Content '$keyFile' 'your-shared-passphrase-here'" -ForegroundColor Yellow
        Write-Host "  Use the SAME passphrase on every machine." -ForegroundColor Yellow
        return $null
    }
    $passphrase = (Get-Content $keyFile -Raw).Trim()
    if (-not $passphrase) {
        Write-Host "  .env.key is empty -- add a passphrase" -ForegroundColor Red
        return $null
    }

    $sha = [System.Security.Cryptography.SHA256]::Create()
    return $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($passphrase))
}

function Protect-PolySaaSEnv {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot
    )

    $envFile = Join-Path $RepoRoot ".env"
    $encFile = Join-Path $RepoRoot ".env.enc"

    if (-not (Test-Path $envFile)) {
        Write-Host "  No .env to encrypt" -ForegroundColor DarkGray
        return $false
    }

    $key = _Get-EnvAesKey -RepoRoot $RepoRoot
    if (-not $key) { return $false }

    $plainBytes = [System.IO.File]::ReadAllBytes($envFile)

    $aes = [System.Security.Cryptography.Aes]::Create()
    $aes.Key = $key
    $aes.GenerateIV()
    $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
    $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7

    $encryptor = $aes.CreateEncryptor()
    $cipherBytes = $encryptor.TransformFinalBlock($plainBytes, 0, $plainBytes.Length)

    # File format: 16-byte IV + ciphertext
    $outBytes = $aes.IV + $cipherBytes
    [System.IO.File]::WriteAllBytes($encFile, $outBytes)

    $aes.Dispose()

    $sz = $plainBytes.Length
    Write-Host "  .env encrypted -> .env.enc ($sz bytes)" -ForegroundColor Green
    return $true
}

function Unprotect-PolySaaSEnv {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot
    )

    $encFile = Join-Path $RepoRoot ".env.enc"
    $envFile = Join-Path $RepoRoot ".env"

    if (-not (Test-Path $encFile)) {
        Write-Host "  No .env.enc in repo -- nothing to decrypt" -ForegroundColor DarkGray
        return $false
    }

    $key = _Get-EnvAesKey -RepoRoot $RepoRoot
    if (-not $key) { return $false }

    # Skip if .env is already newer than .env.enc (local edits not yet encrypted)
    if ((Test-Path $envFile)) {
        $envTs  = (Get-Item $envFile).LastWriteTimeUtc
        $encTs  = (Get-Item $encFile).LastWriteTimeUtc
        if ($envTs -gt $encTs) {
            Write-Host "  .env is newer than .env.enc -- skipping decrypt (encrypt before push)" -ForegroundColor DarkYellow
            return $false
        }
    }

    $allBytes = [System.IO.File]::ReadAllBytes($encFile)
    if ($allBytes.Length -lt 17) {
        Write-Host "  .env.enc too small or corrupt" -ForegroundColor Red
        return $false
    }

    $iv = $allBytes[0..15]
    $cipherBytes = $allBytes[16..($allBytes.Length - 1)]

    $aes = [System.Security.Cryptography.Aes]::Create()
    $aes.Key = $key
    $aes.IV = $iv
    $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
    $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7

    try {
        $decryptor = $aes.CreateDecryptor()
        $plainBytes = $decryptor.TransformFinalBlock($cipherBytes, 0, $cipherBytes.Length)
    } catch {
        Write-Host "  Decryption failed -- wrong passphrase in .env.key?" -ForegroundColor Red
        $aes.Dispose()
        return $false
    }

    $aes.Dispose()

    [System.IO.File]::WriteAllBytes($envFile, $plainBytes)
    $sz = $plainBytes.Length
    Write-Host "  .env.enc decrypted -> .env ($sz bytes)" -ForegroundColor Green
    return $true
}
