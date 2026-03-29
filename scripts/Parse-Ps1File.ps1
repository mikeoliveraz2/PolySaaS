param([Parameter(Mandatory)][string]$Path)
$err = $null
$tok = $null
[void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $Path), [ref]$tok, [ref]$err)
if ($err) {
    $err | ForEach-Object { "$($_.Message) @ $($_.Extent.StartLineNumber):$($_.Extent.StartColumnNumber)" }
    exit 1
}
Write-Host "OK $Path"
