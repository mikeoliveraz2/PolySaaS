# BOM System Summary for Shela & Michael

**Date**: 2026-06-02  
**Purpose**: Explain the Bill of Materials (BOM) system to prevent incomplete commits

---

## What We Built

A **Bill of Materials (BOM)** system for PolySaaS that ensures commits are complete and revertible. This solves the problem of partial commits that can't be reverted.

### The Problem
- **BINGO commit `d191f2a3`** was supposed to be working, but lacked critical bootstrap logic
- **Files were committed separately**, not as a coherent set
- **Reverting failed** because not everything was in the repo
- **Team couldn't understand** which files belonged together

### The Solution
**BOM**: A manifest of **every file** involved in a feature. Before committing:
1. Cross-reference your changes against the BOM
2. Verify all co-dependent files are staged together
3. Run the verification script
4. Commit with confidence that revert will work

---

## Four New Documents Created

### 1. **BOM_MATTERMOST_ACTUAL.md**
**What**: Complete list of files involved in Mattermost passthrough SSO

**Content**:
- 9 layers (handler, forwarding, templates, provisioning, routing, etc.)
- Status of each file (FROZEN, ACTIVE, REFERENCE, LOCKED)
- Why each file matters
- What to do if it changes
- Real-world examples of "incomplete commit" mistakes

**When to Use**:
- Before modifying any passthrough file
- To understand dependencies
- To verify your commit is complete

### 2. **QUICK_REFERENCE_BOM_DISCIPLINE.md**
**What**: Cheat sheet and quick-start guide

**Content**:
- 30-second workflow
- Commit templates
- Example commits (WIP vs BINGO)
- Common mistakes + fixes
- Pre-commit checklist

**When to Use**:
- Every time you commit
- For team training
- As reference during code review

### 3. **GIT_WORKFLOW_BOM_DISCIPLINE.md**
**What**: Complete operational guide for the team

**Content**:
- Step-by-step WIP and BINGO workflows
- How to recover a BINGO state
- Freeze banner rules
- Pre-commit hooks setup
- Troubleshooting guide
- Real-world scenarios

**When to Use**:
- Onboarding new developers
- When processes change
- For policy reference

### 4. **verify_bom.py** (Script)
**What**: Python script that validates commits against the BOM

**Usage**:
```bash
python scripts/verify_bom.py --check-staged
```

**Output**:
- ✅ All ACTIVE files present → commit OK
- ⚠️  Missing files → warning with list
- 🔒 Locked files detected → error (stop commit)
- 📖 Reference files changing → informational

**When to Use**:
- Before every commit
- Optional (workflow still works without it)
- Automated in pre-commit hook (if enabled)

---

## How It Works: The Layers

Mattermost passthrough feature touches **9 layers**. A complete commit must handle ALL layers affected:

```
Layer 1: Handler          (mattermost_handler.py)       [Endpoint-specific]
Layer 2: Forwarding       (forwarding.py)               [Generic shared code]
Layer 3: Admin UI         (admin templates)             [Display only]
Layer 4: Bootstrap        (passthrough_shim.html)       [Token injection]
Layer 5: Client JS        (mattermost_shim.js)          [Request patching]
Layer 6: Provisioning     (mattermost_provisioning_service.py) [Setup]
Layer 7: Routing          (views.py, urls.py)           [Entry points]
Layer 8: Documentation    (BINGO_*.md, BOM_*.md)        [Certification]
Layer 9: Database         (models.py, migrations)       [Schema]
```

**Example**: If you fix bootstrap token format:
- Layer 1: ✅ Modify handler to inject new token format
- Layer 4: ✅ Modify template to write token correctly
- Layer 5: ✅ Modify client shim to read new format
- **All 3 must be in same commit**, or revert will fail

---

## The Checklist: Before Committing

**Quick version** (30 seconds):
```bash
git status                                    # See what changed
python scripts/verify_bom.py --check-staged  # Verify completeness
git commit -m "Fix: [description] per BOM"   # Commit
git show HEAD --name-only                    # Double-check
git push origin main                         # Push
```

**Detailed version** (checklist):
- [ ] Changes tested locally
- [ ] All expected files appear in `git status`
- [ ] No `.bak` or `.current` files staged
- [ ] `verify_bom.py --check-staged` passes
- [ ] Commit message lists every file
- [ ] For BINGO: freeze banners added
- [ ] For BINGO: documentation created
- [ ] `git show HEAD --stat` shows all expected files

---

## Real Example: The Infinite Loop Fix

**Problem**: Mattermost redirects infinitely after plugin auth.

**Files that must change together**:
```
dose/passthrough/handlers/mattermost_handler.py
  - Add mm_idb_booted check (server-side loop break)
  
dose/templates/passthrough_shim.html
  - Add mm_idb_booted query param (client-side signal)
  - Set sessionStorage flag to prevent re-execution
  
documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md
  - New BINGO document certifying the fix
```

**What happens if you only commit the handler?**
- Server-side logic is in place ✅
- Client-side flag NOT sent 🔴
- Loop still happens 💥
- Can't revert (template changes nowhere) 💥

**With BOM**: `verify_bom.py` would say:
```
⚠️  INCOMPLETE FLEXIBLE FILE SET
✅ dose/passthrough/handlers/mattermost_handler.py
❌ dose/templates/passthrough_shim.html (MISSING)

Are you sure you don't need to modify the missing one?
```

---

## Status of This System

| Component | Status | Notes |
|-----------|--------|-------|
| BOM_MATTERMOST_ACTUAL.md | ✅ Ready | 9 layers, all files verified from actual codebase |
| QUICK_REFERENCE_BOM_DISCIPLINE.md | ✅ Ready | Cheat sheet for team |
| GIT_WORKFLOW_BOM_DISCIPLINE.md | ✅ Ready | Complete operational guide |
| verify_bom.py (script) | ✅ Ready | Validates staged files against BOM |
| pre-commit hook | ✅ Ready but optional | Automatically blocks incomplete commits |
| commit template | ✅ Ready but optional | Guides message creation |

**None of this requires code changes to the main project.** These are pure documentation + tooling.

---

## Rollout Plan

### Phase 1: Documentation (TODAY)
- ✅ Create BOM_MATTERMOST_ACTUAL.md
- ✅ Create QUICK_REFERENCE_BOM_DISCIPLINE.md
- ✅ Create GIT_WORKFLOW_BOM_DISCIPLINE.md
- ✅ Create verify_bom.py
- Stage and commit these 4 files together

### Phase 2: Team Adoption
- Share BOM with Shela & Michael
- Try on next Mattermost commit (use as guide, don't enforce)
- Adjust based on feedback

### Phase 3: Full Enforcement (Optional)
- Install pre-commit hook: `cp scripts/pre-commit-bom-check.sh .git/hooks/pre-commit`
- Configure template: `git config commit.template scripts/commit-template-mattermost.txt`
- Now every commit is guided/verified

---

## Key Wins

1. **No More Incomplete Commits**: BOM verification catches missing files
2. **Easier Debugging**: BOM explains which files go together
3. **Confident Reverts**: "This commit has everything I need"
4. **Team Alignment**: Everyone knows the rules
5. **Audit Trail**: Commit messages now reference the BOM

---

## Next Steps

1. **Review the BOM documents** (especially BOM_MATTERMOST_ACTUAL.md)
2. **Try the verify_bom.py script** on your next commit
3. **Give feedback** on clarity/usefulness
4. **Adopt for Odoo/Nextcloud** (other bundled apps) when needed
5. **Optional**: Install pre-commit hook if you want automation

---

## Questions for Shela

1. **Does this approach make sense?** (Or should we organize differently?)
2. **Should we create BOMs for Odoo, Nextcloud, etc. now?** (Or just Mattermost for now?)
3. **Do you want the pre-commit hook enabled?** (Automatic validation vs optional checking?)
4. **Should BINGO commits always require freeze banners?** (Or only for critical files?)

---

**Summary**: You now have a system to ensure commits are complete and revertible. Use it before pushing, especially for BINGO states.
