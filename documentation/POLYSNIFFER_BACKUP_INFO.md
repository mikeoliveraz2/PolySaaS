# PolySniffer Backup Information

## Last Known Working State
- **Commit**: `47e9c79` (HEAD)
- **Message**: "Fix PolySniffer v0.dev proxy: base tag, compression, CSP, and static asset bypass"
- **Date**: November 24, 2025
- **Backup File**: `dose/polysniffer/views.py.backup_HEAD`

## Current State
- **File**: `dose/polysniffer/views.py` (with uncommitted changes)
- **Backup**: `dose/polysniffer/views.py.current_working` (current working copy)

## Rollback Procedure

### To roll back to last committed state:
```powershell
# Restore from HEAD backup
cp dose/polysniffer/views.py.backup_HEAD dose/polysniffer/views.py

# OR use git to restore
git checkout HEAD -- dose/polysniffer/views.py
```

### To roll back to current working state:
```powershell
cp dose/polysniffer/views.py.current_working dose/polysniffer/views.py
```

## Changes Made (Uncommitted)
The current working file has extensive changes to fix static asset loading:
- Early static asset detection and bypass
- Multiple passes of URL rewriting (regex + BeautifulSoup)
- Client-side URL interception
- Final response content rewriting

## Iteration Strategy
1. **Try**: Make a small, focused change
2. **Test**: Verify it works or identify the failure
3. **Fail**: If it breaks, roll back immediately
4. **Try Different**: Make a different approach

## Next Steps
- Start with the backup state
- Make one small change at a time
- Test after each change
- Roll back if it breaks

