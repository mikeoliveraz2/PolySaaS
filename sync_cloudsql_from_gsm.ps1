param(
    [string]$EnvPath = ".env",
    [string]$ProjectId = "application-integration-4524",
    [switch]$SkipProjectSet,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"

function Get-SecretValue {
    param([Parameter(Mandatory = $true)][string]$Name)

    $raw = gcloud secrets versions access latest --secret=$Name 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read secret '$Name'. Ensure it exists and your gcloud auth has access."
    }

    return ($raw -join "`n").Trim()
}

function Set-EnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $pattern = "(?m)^" + [regex]::Escape($Key) + "=.*$"

    if ([regex]::IsMatch($Text, $pattern)) {
        return [regex]::Replace($Text, $pattern, { param($m) "$Key=$Value" })
    }

    $trimmed = $Text.TrimEnd("`r", "`n")
    if ([string]::IsNullOrEmpty($trimmed)) {
        return "$Key=$Value`r`n"
    }

    return "$trimmed`r`n$Key=$Value`r`n"
}

if (-not (Test-Path $EnvPath)) {
    throw "Env file not found at '$EnvPath'."
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "gcloud CLI is not installed or not available on PATH."
}

if (-not $SkipProjectSet) {
    gcloud config set project $ProjectId | Out-Null
}

$dbHost = (Get-SecretValue -Name "db-host") -replace "\s+", ""
$dbPort = (Get-SecretValue -Name "db-port") -replace "\s+", ""
$dbName = (Get-SecretValue -Name "db-name") -replace "\s+", ""
$dbUser = (Get-SecretValue -Name "db-user") -replace "\s+", ""
$dbPassword = Get-SecretValue -Name "dose-db-password"

if ([string]::IsNullOrWhiteSpace($dbHost) -or [string]::IsNullOrWhiteSpace($dbPort) -or [string]::IsNullOrWhiteSpace($dbName) -or [string]::IsNullOrWhiteSpace($dbUser) -or [string]::IsNullOrWhiteSpace($dbPassword)) {
    throw "One or more required secrets are blank."
}

$encodedPassword = [uri]::EscapeDataString($dbPassword)
$databaseUrl = "postgresql://$dbUser`:$encodedPassword@$dbHost`:$dbPort/$dbName"

$content = Get-Content $EnvPath -Raw
$content = Set-EnvValue -Text $content -Key "DB_HOST" -Value $dbHost
$content = Set-EnvValue -Text $content -Key "DB_PORT" -Value $dbPort
$content = Set-EnvValue -Text $content -Key "DB_NAME" -Value $dbName
$content = Set-EnvValue -Text $content -Key "DB_USER" -Value $dbUser
$content = Set-EnvValue -Text $content -Key "DOSE_DB_PASSWORD" -Value $dbPassword
$content = Set-EnvValue -Text $content -Key "DATABASE_URL" -Value $databaseUrl

Set-Content -Path $EnvPath -Value $content -NoNewline

Write-Output "Updated $EnvPath with CloudSQL settings from Secret Manager."
Write-Output "DB_HOST=$dbHost"
Write-Output "DB_PORT=$dbPort"
Write-Output "DB_NAME=$dbName"
Write-Output "DB_USER=$dbUser"

if ($Verify) {
    python manage.py shell -c "from django.conf import settings; from django.db import connection; db=settings.DATABASES['default']; print('CONFIG', db.get('HOST'), db.get('PORT'), db.get('NAME'), db.get('USER')); cur=connection.cursor(); cur.execute('select inet_server_addr()::text, inet_server_port()'); print('LIVE', cur.fetchone())"
}
