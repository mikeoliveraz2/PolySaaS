# Quick Reference: BOM Discipline for Mattermost Passthrough SSO

This guide helps you create complete, revertible commits using the Bill of Materials (BOM).

---

## 🚀 Quick Start: Before Every Commit

```bash
# 1. See what you've changed
git status
git diff --name-only

# 2. Verify against BOM using the verification script
python scripts/verify_bom.py --check-staged

# 3. If BOM check passes, commit with comprehensive message
git commit -m "$(cat scripts/commit-template-mattermost.txt)"

# 4. Verify commit captured everything
git show HEAD --name-only

# 5. Push
git push origin main
```

---

## 📋 The Mattermost Passthrough BOM (Quick Version)

### ✅ ACTIVE (Touch on every major fix)
- `dose/passthrough/handlers/mattermost_handler.py` — Server-side interception

### 🔄 FLEXIBLE (Co-dependent; modify together)
- `dose/templates/passthrough_shim.html` — Bootstrap page + token injection
- `dose/static/js/mattermost_shim.js` — Client-side auth shim

### 📖 REFERENCE (Rarely changed)
- `dose/passthrough/views.py` — Entry point
- `dose/passthrough/middleware.py` — CSRF & auth checks
- `dose/services/mattermost_provisioning.py` — User provisioning
- (and a few others; see full BOM)

### 🔒 LOCKED (Do NOT edit)
- `dose/templates/admin/base_site.html` — FROZEN
- `dose/templates/admin/includes/custom_sidebar.html` — FROZEN

---

## 🛑 Common Mistakes → How to Avoid Them

| Mistake | Why It's Bad | How to Avoid |
|---------|------------|------------|
| Only committing `mattermost_handler.py` | Client-side shim changes not saved; can't revert | Run `verify_bom.py --check-staged` before commit |
| Forgetting to update `passthrough_shim.html` when changing token logic | Template injects old token format; auth fails | Commit message must list EVERY modified file |
| Editing `admin/base_site.html` without permission | Admin templates are FROZEN; breaks other features | Check `admin-templates-locked.mdc` before touching |
| Creating BINGO without freeze banners | Other developers may edit frozen code | Add freeze banner to EVERY file in BINGO commit |
| Not documenting WHY reference files changed | Hard to understand architecture later | Always explain in commit message if reference layer modified |

---

## 📝 Commit Message Template (3-Step)

### Step 1: One-Line Summary
```
[TYPE]: What this commit does (≤50 chars)
```
Examples:
- `🐛 FIX: Break infinite bootstrap redirect loop`
- `✨ FEATURE: Add IDB token injection`
- `✅ BINGO: Mattermost SSO complete — auto-login working`

### Step 2: Detailed Explanation (Optional)
```
Why was this change needed? What problem does it solve?
```

### Step 3: BOM Verification
```
Files Modified (per BOM):
✅ dose/passthrough/handlers/mattermost_handler.py
✅ dose/templates/passthrough_shim.html
✅ dose/static/js/mattermost_shim.js

Verified:
✅ No infinite redirects
✅ Mattermost UI renders
✅ SSO works on first access
```

---

## 🔄 Workflow: From WIP to BINGO

### 1. Creating a WIP Commit (Work In Progress)
```bash
# Modify files (handler, template, shim, etc.)
git add -A
git commit -m "WIP: Fix bootstrap token format

Files Modified:
- dose/passthrough/handlers/mattermost_handler.py (token payload)
- dose/templates/passthrough_shim.html (IDB write format)
- dose/static/js/mattermost_shim.js (credential structure)

Status: Testing locally, handler isolation working, pending team tests"
```

### 2. Testing & Refinement
```bash
# Test the changes locally
# If issues found, modify files and amend (careful!):
git add -A
git commit --amend  # Update WIP commit

# Push to branch
git push origin main  # or your branch
```

### 3. Converting WIP to BINGO (Once Verified)
```bash
# When it's solid, create a BINGO commit
# with freeze banners:

# 1. Add freeze banners to source files (see bingo-freeze.mdc)
# Edit dose/passthrough/handlers/mattermost_handler.py, add:
"""
<!-- THIS CODE IS FROZEN — Mattermost Passthrough BINGO 2026-06-02
 NO CHANGES WITHOUT OWNER PERMISSION
 See: documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md -->
"""

# 2. Create BINGO documentation:
cat > documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md << 'EOF'
# BINGO: Mattermost SSO Auto-Login Working — 2026-06-02

**Commit**: abc1234567
**Date**: 2026-06-02
**Status**: ✅ VERIFIED WORKING

## Files Modified
- dose/passthrough/handlers/mattermost_handler.py
- dose/templates/passthrough_shim.html
- dose/static/js/mattermost_shim.js

## Verification Checklist
✅ Click Mattermost link → immediately redirected to PolySaaS bridge
✅ Bridge auto-submits with plugin token
✅ Mattermost UI loads (no manifest.js 404)
✅ User logged in as correct identity
✅ WebSocket connected (real-time messaging works)
✅ Repeat access works (no "Team Not Found" error)
✅ No infinite redirect loops
✅ Browser console clean

## Known Limitations
None at this time.

## To Revert to This State
git reset --hard abc1234567
EOF

# 3. Commit everything together
git add -A
git commit -m "✅ BINGO: Mattermost SSO — Auto-login working (2026-06-02)

Complete file set (per BOM):
✅ dose/passthrough/handlers/mattermost_handler.py
✅ dose/templates/passthrough_shim.html
✅ dose/static/js/mattermost_shim.js
✅ documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md

Freeze banners applied to all source files.

Verified Working:
✅ No infinite redirects
✅ Full Mattermost UI renders
✅ User authenticated
✅ WebSocket connected
✅ Repeat access successful

THIS COMMIT IS COMPLETE. Revert at any time."

# 4. Push
git push origin main
```

---

## 🔍 How to Verify Your Commit

### Before Pushing
```bash
# Show what files are in the commit
git show HEAD --name-only

# Verify each file
git show HEAD:dose/passthrough/handlers/mattermost_handler.py | head -20
git show HEAD:dose/templates/passthrough_shim.html | head -20

# Check commit message
git log -1 --format=fuller
```

### After Pushing
```bash
# On another machine, verify you can revert
git checkout main
git fetch origin
git reset --hard origin/main
# Now you should have the exact same working state
```

---

## 🆘 If Your Commit Was Incomplete

```bash
# Scenario: You committed only mattermost_handler.py,
# but forgot passthrough_shim.html

# Option 1: Create a follow-up WIP commit
git add dose/templates/passthrough_shim.html
git commit -m "WIP: Add missing passthrough_shim.html changes

(Previous commit abc1234 was incomplete.)"

# Option 2: Amend the previous commit (if not pushed)
git add dose/templates/passthrough_shim.html
git commit --amend  # Add file to previous commit

# Option 3: Force-push if already pushed (use with caution)
git add dose/templates/passthrough_shim.html
git commit --amend
git push origin main --force-with-lease
```

---

## 📚 Full Documentation

- **BOM Document**: `documentation/BOM_MATTERMOST_PASSTHROUGH_SSO.md`
- **Freeze Banner Rules**: `dose/.cursor/rules/bingo-freeze.mdc`
- **Handler Isolation**: `dose/.cursor/rules/passthrough-handler-isolation.mdc`
- **Process Rules**: `dose/.cursor/rules/process-rules.mdc`
- **Previous BINGOs**: `documentation/BINGO_*.md`

---

## ✅ Pre-Commit Checklist

Before running `git commit`, go through this checklist:

```
[ ] All code changes tested locally
[ ] No console errors or warnings
[ ] Mattermost UI renders fully
[ ] SSO redirects work without loops
[ ] WebSocket connected (real-time messaging works)
[ ] Repeat access doesn't cause "Team Not Found" error
[ ] All files in `git status` are expected
[ ] Commit message lists EVERY modified file
[ ] Freeze banners added (if BINGO)
[ ] BINGO documentation created (if BINGO)
[ ] Ready to push
```

---

## 🎯 One More Time: The Golden Rule

> **Commit EVERYTHING needed to reproduce the fix. If you can't revert to this commit and have a working system, the commit was incomplete.**

Every file that changed as part of the fix must be staged and committed together.
