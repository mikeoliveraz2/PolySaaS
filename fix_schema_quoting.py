"""
Fix SET search_path so schema names with hyphens work in PostgreSQL.
Replaces every dynamic schema variable in SET search_path calls with a
double-quoted version so e.g. demo-c becomes "demo-c" in the SQL.

Transforms:
    f"SET search_path TO {schema_name},public;"
into:
    f'SET search_path TO "{schema_name}",public;'
"""
import re, os

prod_files = [
    'dose/views/main.py',
    'mysite/session_tenant_middleware.py',
    'dose/tenant_session.py',
    'dose/context_processors.py',
    'dose/doserequestcontroller.py',
    'dose/admin_base.py',
    'dose/middleware/jazzmin_tenant_theme.py',
    'dose/polysniffer/views/core.py',
    'dose/management/schema_utils.py',
    'dose/services/sniffer_stream_actions.py',
    'dose/mq/queue_monitor.py',
    'dose/mq/mq_response_controller.py',
    'dose/mq/mq_request_controller.py',
    'dose/admin.py',
]

# Match any f-string containing SET search_path TO {expr}
# where expr is NOT already double-quoted
# We'll operate line by line and handle the common patterns

def fix_line(line):
    # Already correct (has "{ or {" pattern = quoted): skip
    if 'search_path TO "{' in line or re.search(r'search_path TO "[^{]', line):
        return line
    # Pattern 1: broken from first run: {"varname"} — literal string, wrong
    # e.g.  f"SET search_path TO {"schema_name"},public;"
    m = re.search(r'(search_path TO )\{"([^"]+)"\}', line)
    if m:
        var = m.group(2)
        # Replace {"varname"} with "{varname}" and fix outer quotes
        # The full f"..." needs outer quotes changed to f'...'
        line = line.replace(
            'f"SET search_path TO {"' + var + '"}',
            'f\'SET search_path TO "{' + var + '}"'
        )
        line = line.replace(
            'f"SET search_path TO {"' + var + '"},',
            'f\'SET search_path TO "{' + var + '}",',
        )
        # Close quote: the trailing " of the original f-string becomes '
        # Handle both ,public; and , pg_catalog; variants
        for suffix in [',public;")', ',public;"))', ', public;")', ', public;"))']:
            if suffix in line:
                line = line.replace(suffix, suffix[:-2] + "')")
        return line

    # Pattern 2: not yet quoted: {schema_name} without surrounding "
    m = re.search(r'(f"[^"]*search_path TO )(\{[^"}][^}]*\})', line)
    if m:
        prefix_in_str = m.group(1)  # f"...SET search_path TO 
        expr = m.group(2)           # {schema_name}
        inner = expr[1:-1]          # schema_name
        # Replace the whole pattern
        old = prefix_in_str + expr
        new = prefix_in_str.replace('f"', "f'", 1) + '"' + expr + '"'
        line = line.replace(old, new, 1)
        # Fix closing quote
        for suffix in [',public;")', ',public;"))','  public;")', ', public;"))', ';")']:
            if suffix in line:
                line = line.replace(suffix, suffix[:-2] + "')")
        return line
    return line

fixed_files = []
for fpath in prod_files:
    if not os.path.exists(fpath):
        print(f'  skip: {fpath}')
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.splitlines(keepends=True)
    new_lines = [fix_line(l) for l in lines]
    new_content = ''.join(new_lines)
    if new_content != content:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        fixed_files.append(fpath)
        print(f'FIXED: {fpath}')
        # Show what changed
        for i, (old, new) in enumerate(zip(lines, new_lines)):
            if old != new:
                print(f'  line {i+1}: {old.rstrip()} -> {new.rstrip()}')
    else:
        print(f'  ok: {fpath}')

print(f'\nTotal fixed: {len(fixed_files)}')
