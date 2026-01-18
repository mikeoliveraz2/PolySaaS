<#
.SYNOPSIS
    Copies all enabled PassThroughEndpoint rows from the public schema into every tenant schema.
    Also sets the `trigger_path_length` field for fast longest‑prefix matching.

.USAGE
    1. Save this file as:  C:\path\to\project\migrate_passthrough_to_all_schemas.ps1
    2. Open PowerShell in the project root
    3. Run:  .\migrate_passthrough_to_all_schemas.ps1
#>

# -------------------------------------------------
# 1. CONFIG – change only if your paths differ
# -------------------------------------------------
$ProjectRoot   = "C:\Users\PC\OneDrive\Documents\GitHub\DoseV3MasterSaaS-main-main"
$PythonExe     = "$ProjectRoot\.venv\Scripts\python.exe"
$ManagePy      = "$ProjectRoot\manage.py"
$ScriptName    = "migrate_passthrough_to_all_schemas"

# -------------------------------------------------
# 2. Verify files exist
# -------------------------------------------------
if (-not (Test-Path $PythonExe))   { Write-Error "Python not found: $PythonExe"; exit 1 }
if (-not (Test-Path $ManagePy))    { Write-Error "manage.py not found: $ManagePy"; exit 1 }

# -------------------------------------------------
# 3. Create the Django script (inline, no extra file needed)
# -------------------------------------------------
$DjangoScript = @'
from django_tenants.utils import get_tenant_model, get_public_schema_name
from dose.models import PassThroughEndpoint
import django, sys, os

Tenant = get_tenant_model()

def migrate():
    public_schema = get_public_schema_name()
    public_tenant = Tenant.objects.get(schema_name=public_schema)
    public_eps = PassThroughEndpoint.objects.using(public_schema).filter(is_enabled=True)

    print(f"Found {public_eps.count()} enabled endpoint(s) in public schema.")

    tenants = Tenant.objects.exclude(schema_name=public_schema)
    total = tenants.count()
    for idx, tenant in enumerate(tenants, 1):
        print(f"[{idx}/{total}] Migrating to tenant: {tenant.schema_name} ...")
        try:
            with tenant:
                for ep in public_eps:
                    length = len(ep.trigger_path or "")
                    PassThroughEndpoint.objects.update_or_create(
                        tenant=tenant,
                        trigger_path=ep.trigger_path,
                        defaults={
                            "endpoint_url": ep.endpoint_url,
                            "is_enabled": ep.is_enabled,
                            "trigger_path_length": length,
                        },
                    )
            print(f"   Done: {tenant.schema_name}")
        except Exception as e:
            print(f"   ERROR in {tenant.schema_name}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
    django.setup()
    migrate()
'@

# Write script to a temp file (PowerShell can’t pipe multi‑line Python directly)
$TempPy = [System.IO.Path]::GetTempFileName() -replace '\.tmp$','.py'
Set-Content -Path $TempPy -Value $DjangoScript -Encoding UTF8

# -------------------------------------------------
# 4. Run the migration
# -------------------------------------------------
Write-Host "`nStarting PassThroughEndpoint migration to all tenant schemas..." -ForegroundColor Cyan

& $PythonExe $ManagePy runscript $TempPy --script-args noinput

$exitCode = $LASTEXITCODE
Remove-Item $TempPy -Force

if ($exitCode -eq 0) {
    Write-Host "`nMigration completed successfully!" -ForegroundColor Green
} else {
    Write-Error "Migration failed with exit code $exitCode"
    exit $exitCode
}