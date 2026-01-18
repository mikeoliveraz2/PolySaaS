#!/usr/bin/env python3
"""Diagnostic: parse mysite/settings.py to extract MIDDLEWARE and test importing each module.

Run with the project's Python (inside venv) from repo root:
python scripts/check_middleware_imports.py
"""
import ast
import importlib
import os
import sys
import traceback

HERE = os.path.dirname(os.path.dirname(__file__))
SETTINGS_PATH = os.path.join(HERE, 'mysite', 'settings.py')

def load_middleware_list(path):
    src = open(path, 'r', encoding='utf-8').read()
    tree = ast.parse(src, filename=path)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if getattr(target, 'id', None) == 'MIDDLEWARE':
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        # fallback: try to evaluate common list/tuple structures
                        try:
                            return [ast.literal_eval(elt) for elt in node.value.elts]
                        except Exception:
                            raise
    raise RuntimeError('MIDDLEWARE assignment not found in settings.py')

def test_imports(middleware_list):
    results = []
    for entry in middleware_list:
        if not isinstance(entry, str):
            results.append((entry, 'SKIP (not a string)'))
            continue
        module_part = entry.rsplit('.', 1)[0]
        print(f"Testing import of module: {module_part}  (from '{entry}')")
        try:
            importlib.import_module(module_part)
            results.append((entry, 'OK'))
        except Exception as e:
            tb = traceback.format_exc()
            results.append((entry, f'FAIL: {type(e).__name__}: {e}\n{tb}'))
    return results

def main():
    print('Reading settings:', SETTINGS_PATH)
    middleware = load_middleware_list(SETTINGS_PATH)
    print('Found', len(middleware), 'middleware entries')
    results = test_imports(middleware)
    print('\n--- Results ---')
    for entry, status in results:
        print(entry, '->', status.splitlines()[0])
    # print failures in full
    print('\n--- Failures (details) ---')
    for entry, status in results:
        if not status.startswith('OK') and not status.startswith('SKIP'):
            print('\nEntry:', entry)
            print(status)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
