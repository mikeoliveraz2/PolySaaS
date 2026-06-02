# Git Workflow for PolySaaS — BOM-Enforced Commits

**For**: Michael, Shela, and the PolySaaS team  
**Status**: Operational guide for disciplined commits  
**Updated**: 2026-06-02

---

## The Problem We're Solving

Previous incomplete commits made it **impossible to revert to a working state**. Example:
- Commit `d191f2a3` claimed to be working but lacked critical bootstrap logic
- Files were committed separately, not as a coherent set
- BINGO documentation didn't list all files actually needed
- Result: Reverting failed because not everything was committed

**This workflow prevents that.**

---

## The Solution: BOM-Enforced Commits

Every commit on Mattermost passthrough (or similar features) is now **verified against a Bill of Materials** to ensure:
1. ✅ All co-dependent files staged together
2. ✅ No orphaned changes (file A changed but file B not)
3. ✅ Commit message lists EVERY file involved
4. ✅ BINGO commits include freeze banners
5. ✅ Revert is guaranteed to work

---

## Quick Workflow

### Step 1: Make Your Changes
```bash
cd d:\PolySaaS

# Edit handler, templates, services, etc.
# (editor or whatever)
```

### Step 2: Stage Everything
```bash
git add -A
git status  # Verify only expected files appear
```

### Step 3: Verify Against BOM
```bash
python scripts/verify_bom.py --check-staged
```

**Output will show**:
- ✅ Active files present
- ⚠️  Flexible files incomplete (if any)
- 📖 Reference files being modified
- 🔒 Locked files (STOP if any!)

### Step 4: Create Comprehensive Commit Message
```bash
# Option A: Use the template
git commit

# Option B: Write directly
git commit -m "Fix: Bootstrap token format (per BOM)

Modified Files:
✅ dose/passthrough/handlers/mattermost_handler.py
✅ dose/templates/passthrough_shim.html

Verified:
✅ Token written to IDB
✅ No errors in console"
```

### Step 5: Verify Commit Captured Everything
```bash
git show HEAD --name-only
git show HEAD --stat

# You should see ALL expected files in the diff
```

### Step 6: Push (Pull First!)
```bash
git pull origin main  # Pick up any changes from laptop/other machine
git push origin main
```

---

## BINGO Commits (Verified Working State)

When you have a **confirmed working version** (SSO works, no loops, UI renders):

### Step 1: Create BINGO Documentation
```bash
# Create documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_YYYY-MM-DD.md

cat > documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md << 'EOF'
# BINGO: Mattermost SSO — Auto-Login Working

**Commit**: (you'll fill this in after commit)  
**Date**: 2026-06-02  
**Verified By**: [Your name]

## Files Modified (per BOM)
- dose/passthrough/handlers/mattermost_handler.py
- dose/templates/passthrough_shim.html
- documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md

## Verification Checklist
✅ Mattermost SSO link redirects to PolySaaS bridge  
✅ Bridge auto-submits with token  
✅ Mattermost UI loads fully (no manifest.js 404)  
✅ User logged in as correct identity  
✅ WebSocket connected  
✅ Repeat access works (no "Team Not Found")  
✅ No infinite redirects  
✅ Browser console clean

## Known Limitations
None at this time.

## Recovery
To revert to this state:
```bash
git reset --hard <commit-hash>
```
EOF
```

### Step 2: Add Freeze Banners to Source Files
```bash
# Edit dose/passthrough/handlers/mattermost_handler.py
# Add at the very top (after any shebang/docstring):

# ============================================================================
# THIS CODE IS FROZEN — NO CHANGES WITHOUT OWNER PERMISSION
# BINGO: Mattermost Passthrough SSO (2026-06-02)
# Commit: <hash>
# See: documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md
# ============================================================================

# Then also add to dose/templates/passthrough_shim.html:
<!-- THIS CODE IS FROZEN — NO CHANGES WITHOUT OWNER PERMISSION
     BINGO: Mattermost Passthrough SSO (2026-06-02)
     Commit: <hash>
     See: documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md
 -->
```

### Step 3: Stage Everything (Including Documentation + Banners)
```bash
git add -A
git status  # Should show: documentation/BINGO_*.md, updated handlers, templates
```

### Step 4: Verify BOM (Should Pass)
```bash
python scripts/verify_bom.py --check-staged
```

### Step 5: Create BINGO Commit
```bash
git commit -m "✅ BINGO: Mattermost SSO — Auto-Login Working (2026-06-02)

Complete File Set (per BOM_MATTERMOST_ACTUAL.md):
✅ dose/passthrough/handlers/mattermost_handler.py
✅ dose/templates/passthrough_shim.html
✅ documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md

Freeze Banners:
✅ Applied to dose/passthrough/handlers/mattermost_handler.py
✅ Applied to dose/templates/passthrough_shim.html

Verified Working:
✅ SSO redirect → PolySaaS bridge
✅ Token injection successful
✅ Mattermost UI loads
✅ WebSocket connected
✅ Real-time messaging works
✅ Repeat access successful (no Team Not Found)
✅ No infinite loops
✅ Browser console clean

THIS IS A COMPLETE, REVERTIBLE COMMIT.
All files needed to reproduce this state are included.
Revert at any time via: git reset --hard <hash>"
```

### Step 6: Verify Commit
```bash
git log -1 --format=fuller
git show HEAD --stat

# You should see:
# - documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md
# - dose/passthrough/handlers/mattermost_handler.py (with freeze banner)
# - dose/templates/passthrough_shim.html (with freeze banner)
```

### Step 7: Push
```bash
git pull origin main
git push origin main
```

---

## Recovery: Reverting to a BINGO

```bash
# Find the BINGO commit
git log --oneline | grep BINGO

# Output: abc1234 ✅ BINGO: Mattermost SSO — Auto-Login Working

# Hard reset to that commit
git reset --hard abc1234

# Verify you got everything
git log -1 --stat
git status  # Should show "nothing to commit, working tree clean"

# You now have the exact working state from that BINGO
```

---

## When You Edit a FROZEN File

If you need to modify a file with a freeze banner:

### Option A: Ask Permission First
```
"I need to modify dose/passthrough/handlers/mattermost_handler.py
(currently frozen per BINGO 2026-06-02). The change is: [describe].
OK to proceed?"
```

### Option B: Remove Freeze & Document
```bash
# Edit the file (remove freeze banner if needed)
git add <file>
git commit -m "WIP: Modify frozen handler (with approval from Shela)

Reason: [describe why freeze needed to be removed]

Previous BINGO: 2026-06-02 (abc1234)
This commit intentionally breaks freeze.
Next BINGO should re-verify all functionality."
```

---

## Preventing Future Incomplete Commits

### Use the Pre-Commit Hook (Optional)
```bash
# Install the hook (only need to do once)
cp scripts/pre-commit-bom-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Now every `git commit` will verify BOM automatically
# If commit is incomplete, it will reject (show warning)
# To force commit (NOT recommended): git commit --no-verify
```

### Use the Commit Template
```bash
# Configure git to use our template
git config commit.template scripts/commit-template-mattermost.txt

# Now every `git commit` shows the template in your editor
# Fill it out, save, commit is created
```

---

## Checklists

### Before ANY Commit
```
[ ] git status shows only expected files
[ ] No .bak, .current, .old files staged
[ ] Commit message lists EVERY modified file
[ ] Cross-reference against BOM_MATTERMOST_ACTUAL.md
[ ] Changes tested locally (Mattermost UI works, no loops, etc.)
[ ] Browser console clean (no persistent errors)
```

### Before BINGO Commit
```
[ ] Documentation created (BINGO_*.md)
[ ] Freeze banners added to source files
[ ] ALL files staged (doc + source + any templates)
[ ] BOM verification passes: python scripts/verify_bom.py --check-staged
[ ] Commit message starts with "✅ BINGO:"
[ ] Revert test (optional): git stash, git reset --hard <hash>, verify working
[ ] Ready to push
```

### After BINGO Commit
```
[ ] git show HEAD --stat shows all expected files
[ ] git log -1 lists commit hash, date, all files
[ ] Documentation reflects actual commit hash
[ ] Push completed
[ ] Announce to team (if applicable)
```

---

## Example: Real-World Scenario

**Scenario**: You fix the "infinite bootstrap loop" by modifying handler and template.

```bash
# 1. Edit files
vim dose/passthrough/handlers/mattermost_handler.py
vim dose/templates/passthrough_shim.html

# 2. Test locally
# (Manually click Mattermost link, verify SSO works, no loops)

# 3. Stage
git add -A
git status
# On branch main
# Changes to be committed:
#   modified: dose/passthrough/handlers/mattermost_handler.py
#   modified: dose/templates/passthrough_shim.html

# 4. Verify BOM
python scripts/verify_bom.py --check-staged
# ✅ BOM verification passed!

# 5. Commit
git commit -m "WIP: Fix infinite bootstrap redirect loop

Modified (per BOM):
✅ dose/passthrough/handlers/mattermost_handler.py (server-side loop check)
✅ dose/templates/passthrough_shim.html (client-side state flag)

Status: Testing locally; handler isolation working; pending team validation"

# 6. Verify commit
git show HEAD --name-only
# dose/passthrough/handlers/mattermost_handler.py
# dose/templates/passthrough_shim.html

# 7. Push
git pull origin main && git push origin main

# 8. If working after team tests, create BINGO
# (Follow "BINGO Commits" section above)
```

---

## Common Mistakes & How to Avoid

| Mistake | How to Avoid | Fix |
|---------|------------|-----|
| Only committing mattermost_handler.py (forgetting bootstrap template) | Run `verify_bom.py --check-staged` before commit | Add missing file: `git add <file>`, then `git commit --amend` |
| Editing admin templates without permission | Check `admin-templates-locked.mdc` before touch | Don't edit. Ask owner first. |
| BINGO commit without freeze banners | Read `bingo-freeze.mdc` before BINGO | Create new BINGO with banners added |
| Committing `.bak` or `.current` files | Run `git status` before staging; verify only tracked files | `git reset HEAD <file.bak>`, then `git clean -fd` |
| BINGO commit that's actually incomplete | Use `verify_bom.py --check-staged` and test revert before push | Document what's missing; create follow-up WIP |

---

## Reference Documents

1. **BOM (Bill of Materials)**: `documentation/BOM_MATTERMOST_ACTUAL.md`  
   — Complete list of ALL files involved in Mattermost feature

2. **Quick Reference**: `documentation/QUICK_REFERENCE_BOM_DISCIPLINE.md`  
   — Cheat sheet for common commit scenarios

3. **Freeze Rules**: `dose/.cursor/rules/bingo-freeze.mdc`  
   — Freeze banner format and requirements

4. **Handler Isolation**: `dose/.cursor/rules/passthrough-handler-isolation.mdc`  
   — Rule: App-specific logic stays in handler, not in shared code

5. **Admin Templates**: `dose/.cursor/rules/admin-templates-locked.mdc`  
   — Admin templates are single-source-of-truth and locked

6. **Process Rules**: `dose/.cursor/rules/process-rules.mdc`  
   — Overall commit discipline and process

---

## Questions?

- **"Can I just commit the handler?"** → Ask yourself: "Are there co-dependent files (template, provisioning, docs) that should move together?" If yes, commit them together.

- **"Should I commit test files?"** → Include if tests changed significantly; optional otherwise.

- **"Should I commit management commands?"** → Only if command behavior is critical to feature; usually skip.

- **"Should I commit .bak files?"** → **NO**. These are temporary backups. Never stage `.bak`, `.current`, `.old` files.

- **"Can I force-push?"** → Only if you're working alone and immediately. Always use `--force-with-lease` to avoid accidents.

---

## Summary

✅ **Stage ALL co-dependent files together**  
✅ **Use BOM to verify completeness**  
✅ **List every file in commit message**  
✅ **For BINGO: add freeze banners + documentation**  
✅ **Test revert before declaring BINGO complete**  

**Golden Rule**: If you can't revert to this commit and have a working system, the commit was incomplete.

---

**Version**: 1.0 (2026-06-02)  
**Status**: Ready for team use  
**Last Updated**: 2026-06-02  
**Maintained By**: Shela & Michael
