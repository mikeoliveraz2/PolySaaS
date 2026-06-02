#!/usr/bin/env python3
"""
BOM Verification Script for PolySaaS Mattermost Passthrough SSO

Purpose: Verify that a commit includes all necessary files from the Bill of Materials
         before pushing a WIP or BINGO commit.

Usage:
  python verify_bom.py --check-staged       # Verify all staged files against BOM
  python verify_bom.py --check-modified     # Verify all modified files against BOM
  python verify_bom.py --list-bom           # Print the BOM
  python verify_bom.py --strict             # Fail if ANY active file is missing from staged
"""

import subprocess
import sys
from pathlib import Path

# Bill of Materials for Mattermost Passthrough SSO
BOM_ACTIVE = [
    # Core Handler Layer (ACTIVE - touch on every major fix)
    "dose/passthrough/handlers/mattermost_handler.py",
]

BOM_ACTIVE_FLEXIBLE = [
    # These should be modified together, but may not all change in every commit
    "dose/templates/passthrough_shim.html",
    "dose/static/js/mattermost_shim.js",
]

BOM_REFERENCE = [
    # Reference layer (rarely changed; only if architecture/routing changes)
    "dose/passthrough/handlers/handler_base.py",
    "dose/passthrough/views.py",
    "dose/passthrough/middleware.py",
    "dose/passthrough/registry.py",
    "dose/passthrough/urls.py",
    "dose/urls.py",
    "dose/settings.py",
    "dose/admin.py",
    "dose/services/mattermost_provisioning.py",
]

BOM_LOCKED = [
    # FROZEN - Do NOT edit without permission
    "dose/templates/admin/base_site.html",
    "dose/templates/admin/includes/custom_sidebar.html",
]


def run_git_cmd(cmd):
    """Run a git command and return output lines."""
    try:
        result = subprocess.run(
            f"git {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    except Exception as e:
        print(f"❌ Error running git command: {e}")
        return []


def get_staged_files():
    """Get list of staged files."""
    return run_git_cmd("diff --cached --name-only")


def get_modified_files():
    """Get list of modified files (staged + unstaged)."""
    return run_git_cmd("diff --name-only")


def check_locked_files(files):
    """Warn if any locked files are being modified."""
    locked_modified = [f for f in files if f in BOM_LOCKED]
    if locked_modified:
        print("\n⚠️  WARNING: FROZEN/LOCKED files detected in commit:")
        for f in locked_modified:
            print(f"   🔒 {f}")
        print("   These files cannot be modified without explicit owner permission.")
        print("   See: dose/.cursor/rules/admin-templates-locked.mdc")
        return False
    return True


def check_active_files(files):
    """Check if all ACTIVE files are present."""
    active_missing = [f for f in BOM_ACTIVE if f not in files]
    if active_missing:
        print("\n⚠️  MISSING ACTIVE FILES:")
        for f in active_missing:
            print(f"   ❌ {f}")
        return False
    return True


def check_flexible_files(files):
    """Warn if flexible files are incomplete."""
    flexible_present = [f for f in files if f in BOM_ACTIVE_FLEXIBLE]
    if len(flexible_present) > 0 and len(flexible_present) < len(BOM_ACTIVE_FLEXIBLE):
        print("\n⚠️  INCOMPLETE FLEXIBLE FILE SET (co-dependent files):")
        print("   These files typically change together:")
        for f in BOM_ACTIVE_FLEXIBLE:
            status = "✅" if f in files else "❌"
            print(f"   {status} {f}")
        print("\n   Are you sure you don't need to modify the missing ones?")
        return False
    return True


def check_reference_files(files):
    """Warn if unexpected reference files are modified."""
    ref_modified = [f for f in files if f in BOM_REFERENCE]
    if ref_modified:
        print("\n⚠️  REFERENCE FILES MODIFIED (usually unchanged):")
        for f in ref_modified:
            print(f"   ⚠️  {f}")
        print("   Document why these changed in your commit message.")
        return True
    return True


def print_bom():
    """Print the full BOM."""
    print("\n📋 BILL OF MATERIALS (BOM) - Mattermost Passthrough SSO\n")
    
    print("✅ ACTIVE (modify on every major fix):")
    for f in BOM_ACTIVE:
        print(f"   • {f}")
    
    print("\n🔄 FLEXIBLE (co-dependent, modify together):")
    for f in BOM_ACTIVE_FLEXIBLE:
        print(f"   • {f}")
    
    print("\n📖 REFERENCE (rarely changed):")
    for f in BOM_REFERENCE:
        print(f"   • {f}")
    
    print("\n🔒 LOCKED (FROZEN - do NOT edit):")
    for f in BOM_LOCKED:
        print(f"   • {f}")


def verify_staged(strict=False):
    """Verify staged files against BOM."""
    staged = get_staged_files()
    
    if not staged:
        print("❌ No staged files. Nothing to commit.")
        return False
    
    print(f"\n📦 Checking {len(staged)} staged file(s) against BOM...\n")
    
    # Check for locked files
    if not check_locked_files(staged):
        return False
    
    # Check for active files (strict mode)
    if strict:
        if not check_active_files(staged):
            return False
    
    # Check for flexible files
    if not check_flexible_files(staged):
        return False
    
    # Check reference files
    check_reference_files(staged)
    
    print("\n✅ BOM verification passed!")
    print(f"\nStaged files ({len(staged)}):")
    for f in staged:
        print(f"   • {f}")
    
    return True


def verify_modified():
    """Verify all modified files against BOM."""
    modified = get_modified_files()
    
    if not modified:
        print("✅ No modified files. Working tree clean.")
        return True
    
    print(f"\n📦 Checking {len(modified)} modified file(s) against BOM...\n")
    
    # Check for locked files
    if not check_locked_files(modified):
        return False
    
    # Check reference files
    check_reference_files(modified)
    
    print("\n📋 Modified files:")
    for f in modified:
        if f in BOM_ACTIVE:
            print(f"   ✅ (ACTIVE) {f}")
        elif f in BOM_ACTIVE_FLEXIBLE:
            print(f"   🔄 (FLEXIBLE) {f}")
        elif f in BOM_REFERENCE:
            print(f"   📖 (REFERENCE) {f}")
        else:
            print(f"   ❓ (UNKNOWN) {f}")
    
    return True


def main():
    """Parse arguments and run verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BOM verification for Mattermost passthrough SSO")
    parser.add_argument("--check-staged", action="store_true", help="Check staged files")
    parser.add_argument("--check-modified", action="store_true", help="Check all modified files")
    parser.add_argument("--list-bom", action="store_true", help="Print the BOM")
    parser.add_argument("--strict", action="store_true", help="Strict mode: fail if any ACTIVE file missing")
    
    args = parser.parse_args()
    
    if args.list_bom:
        print_bom()
        return 0
    
    if args.check_staged:
        success = verify_staged(strict=args.strict)
        return 0 if success else 1
    
    if args.check_modified:
        success = verify_modified()
        return 0 if success else 1
    
    # Default: check staged
    success = verify_staged(strict=args.strict)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
