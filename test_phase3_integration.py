#!/usr/bin/env python
"""
Phase 3 Integration Test: Complete Multi-App Token Strategy System

This test verifies:
1. All individual strategies work (Mattermost, Nextcloud, Odoo)
2. Factory pattern correctly routes to appropriate strategies
3. Mattermost handler backward compatibility (uses strategy internally)
4. Extension mechanism is flexible for new apps

Run directly: python test_phase3_integration.py
"""

import os
import sys
import subprocess

print("\n" + "="*70)
print("[PHASE 3 INTEGRATION] Multi-App Token Refresh Strategy System")
print("="*70 + "\n")

tests = [
    ("test_phase3_strategies.py", "Token Refresh Strategies"),
    ("test_phase2_token_refresh.py", "Phase 2 Backward Compatibility (Unit Tests)"),
    ("test_phase2_e2e.py", "Phase 2 Backward Compatibility (E2E Test)"),
]

failed_tests = []
passed_tests = []

for test_file, description in tests:
    print(f"\n[RUNNING] {description}")
    print(f"  File: {test_file}")
    print("-" * 70)
    
    result = subprocess.run(
        ["python", test_file],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True
    )
    
    # Check for success markers in output
    output = result.stdout + result.stderr
    
    if "[SUCCESS]" in output and result.returncode == 0:
        # Count test results
        ok_count = output.count("[OK]")
        print(f"  [PASSED] {description} ({ok_count} assertions)")
        passed_tests.append((test_file, description, ok_count))
    else:
        print(f"  [FAILED] {description}")
        print(f"  Return code: {result.returncode}")
        # Show last few lines of output for debugging
        lines = (result.stdout + result.stderr).split('\n')
        for line in lines[-10:]:
            if line.strip():
                print(f"    {line}")
        failed_tests.append((test_file, description))

# Print summary
print("\n" + "="*70)
print("[PHASE 3 INTEGRATION SUMMARY]")
print("="*70)

print(f"\nTests Passed: {len(passed_tests)}/{len(tests)}")
for test_file, description, ok_count in passed_tests:
    print(f"  [OK] {description} ({ok_count} assertions)")

if failed_tests:
    print(f"\nTests Failed: {len(failed_tests)}/{len(tests)}")
    for test_file, description in failed_tests:
        print(f"  [FAIL] {description}")
    print("\n" + "="*70)
    print("[RESULT] PHASE 3 INTEGRATION INCOMPLETE")
    print("="*70 + "\n")
    sys.exit(1)
else:
    print("\n" + "="*70)
    print("[SUCCESS] PHASE 3 INTEGRATION COMPLETE")
    print("="*70)
    print("\nPhase 3 Deliverables:")
    print("  1. TokenRefreshStrategy abstract base class")
    print("  2. MattermostTokenRefreshStrategy implementation")
    print("  3. NextcloudTokenRefreshStrategy implementation")
    print("  4. OdooTokenRefreshStrategy implementation")
    print("  5. TokenRefreshStrategyFactory with registry pattern")
    print("  6. Mattermost handler refactored to use strategy factory")
    print("  7. Full backward compatibility maintained")
    print("  8. Extensible architecture for future apps")
    print("\nKey Features:")
    print("  - Pluggable strategy pattern for token refresh")
    print("  - Clean factory interface for adding new apps")
    print("  - Encrypted session token storage (from Phase 1)")
    print("  - Automatic token refresh on 401 errors (from Phase 2)")
    print("  - Multi-app support: Mattermost, Nextcloud, Odoo")
    print("\n" + "="*70 + "\n")
    sys.exit(0)
