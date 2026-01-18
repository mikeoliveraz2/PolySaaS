#!/usr/bin/env python
"""
Script to identify and report all print statements and OSTicket references
in external_passthrough_middleware.py for manual cleanup.

This script helps catalog issues WITHOUT making changes, so we can prioritize
and handle them systematically.
"""

import re
from pathlib import Path

middleware_path = Path(__file__).parent / "mysite" / "external_passthrough_middleware.py"

print("=" * 80)
print("MIDDLEWARE ANALYSIS REPORT")
print("=" * 80)

with open(middleware_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all print statements
print("\nPRINT STATEMENTS TO REPLACE:")
print("-" * 80)
print_matches = []
for i, line in enumerate(lines, 1):
    if re.search(r'\bprint\s*\(', line):
        print_matches.append((i, line.rstrip()))
        print(f"Line {i}: {line.rstrip()}")

print(f"\nTotal: {len(print_matches)} print statements")

# Find all OSTicket references
print("\n\nOSTICKET REFERENCES (DEAD CODE) TO REMOVE:")
print("-" * 80)
osticket_matches = []
for i, line in enumerate(lines, 1):
    if re.search(r'\bosticket\b|\bOSTicket\b', line, re.IGNORECASE):
        osticket_matches.append((i, line.rstrip()))
        # Only show non-trivial matches (not just comments explaining the system)
        if 'OSTicket and other' not in line and 'osticket' in line.lower():
            print(f"Line {i}: {line.rstrip()}")

print(f"\nTotal: {len(osticket_matches)} OSTicket references")

# Find complex functions (>50 lines)
print("\n\nCOMPLEX FUNCTIONS (CANDIDATES FOR EXTRACTION):")
print("-" * 80)

# Find all function definitions
current_func = None
func_start_line = 0
func_lines = 0
complex_funcs = []

for i, line in enumerate(lines, 1):
    if re.match(r'\s{4}def\s+(\w+)\s*\(', line):
        if current_func and func_lines > 50:
            complex_funcs.append((current_func, func_start_line, i - 1, func_lines))

        match = re.match(r'\s{4}def\s+(\w+)\s*\(', line)
        current_func = match.group(1)
        func_start_line = i
        func_lines = 1
    else:
        if current_func:
            func_lines += 1

# Check last function
if current_func and func_lines > 50:
    complex_funcs.append((current_func, func_start_line, len(lines), func_lines))

for func_name, start, end, line_count in complex_funcs:
    print(f"  - {func_name}() [Lines {start}-{end}] ({line_count} lines)")

print(f"\nTotal: {len(complex_funcs)} functions > 50 lines")

# Summary
print("\n\n" + "=" * 80)
print("REFACTORING ROADMAP:")
print("=" * 80)
print("""
PHASE 1 - LOGGING MODERNIZATION:
   * Replace print() calls with logger.debug/info/error
   * Priority: HIGH (required for production)
   * Effort: 2-3 hours

PHASE 2 - DEAD CODE REMOVAL:
   * Remove OSTicket references (no longer supported)
   * Remove commented-out code blocks
   * Priority: HIGH (improves maintainability)
   * Effort: 1-2 hours

PHASE 3 - MODULARIZATION:
   * Extract complex functions into separate files
   * Create modules: odoo_handler.py, form_handler.py, url_mapper.py
   * Priority: MEDIUM (technical debt)
   * Effort: 4-6 hours

RESULT:
   * Current: 2109 lines in 1 file
   * Target: ~400 lines in middleware.py + separate handler modules
   * Benefit: 80% reduction in middleware complexity
""")

print("\n" + "=" * 80)
print("Next steps:")
print("  1. Run phase 1 replacements")
print("  2. Clean up dead code in phase 2")
print("  3. Extract service handlers for phase 3")
print("=" * 80)
