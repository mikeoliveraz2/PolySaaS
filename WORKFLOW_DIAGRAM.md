# Branch Promotion Workflow Diagram

## Visual Guide to Promoting Your Branch

### Current State
```
GitHub Repository: mikeoliveraz2/PolySaaS
│
└── copilot/promote-subset-clean-branch (current)
    ├── website/
    │   ├── PolySaaS-WordPress/
    │   ├── sandbox/
    │   ├── staging/
    │   └── setup vscode for wordpress.md
    └── Initial commits (clean subset)
```

### Goal State
```
GitHub Repository: mikeoliveraz2/PolySaaS
│
└── main (default branch) ← promoted from subset-clean
    ├── website/
    │   ├── PolySaaS-WordPress/
    │   ├── sandbox/
    │   ├── staging/
    │   └── setup vscode for wordpress.md
    ├── README.md
    ├── BRANCH_PROMOTION_GUIDE.md
    └── QUICK_START_PROMOTION.md
```

---

## Method Comparison Flowchart

```
┌─────────────────────────────────────────┐
│   Do you need to promote your branch?   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│     Does 'main' branch exist?            │
└──────┬───────────────────────────┬───────┘
       │ NO                        │ YES
       ▼                           ▼
┌──────────────────┐    ┌─────────────────────────┐
│  Simple Create   │    │  Need to replace main?  │
│                  │    └──────┬─────────┬────────┘
│  1. checkout -b  │           │ YES     │ NO
│  2. push origin  │           ▼         ▼
│  3. Set default  │    ┌─────────┐ ┌─────────┐
└──────────────────┘    │  Reset  │ │  Merge  │
                        │  (force)│ │  (safe) │
                        └─────────┘ └─────────┘
```

---

## Step-by-Step Visual Process

### Method 1: Creating Main (No existing main)

```
Step 1: Checkout New Branch
┌────────────────────────────────────────┐
│ $ git checkout -b main                 │
│                                        │
│ Your branch ─────────────┐             │
│                          ├─> New main  │
│                          │   (same)    │
└────────────────────────────────────────┘

Step 2: Push to Remote
┌────────────────────────────────────────┐
│ $ git push origin main                 │
│                                        │
│ Local main ══════════> Remote main     │
│                                        │
└────────────────────────────────────────┘

Step 3: Set as Default (GitHub UI)
┌────────────────────────────────────────┐
│ Settings → Branches → Default branch   │
│                                        │
│ [copilot/...] ─────> [main] ✓         │
│                                        │
└────────────────────────────────────────┘
```

### Method 2: Pull Request (Safest)

```
Step 1: Create PR on GitHub
┌────────────────────────────────────────┐
│  Base: main  ← Compare: your-branch    │
│                                        │
│  Review Changes                        │
│  ├─ Files changed                      │
│  ├─ Commits                            │
│  └─ Checks                             │
└────────────────────────────────────────┘
           │
           ▼
Step 2: Merge
┌────────────────────────────────────────┐
│  [Merge Pull Request ▼]                │
│   ├─ Create merge commit               │
│   ├─ Squash and merge                  │
│   └─ Rebase and merge                  │
└────────────────────────────────────────┘
           │
           ▼
Step 3: Result
┌────────────────────────────────────────┐
│  main branch now contains all changes  │
│  Your branch can be deleted            │
└────────────────────────────────────────┘
```

### Method 3: Force Replace (Existing main)

```
⚠️  WARNING: Destructive Operation ⚠️

Step 1: Backup
┌────────────────────────────────────────┐
│ $ git branch main-backup-20231223      │
│                                        │
│ main ─────────────> main-backup        │
│  (preserved for safety)                │
└────────────────────────────────────────┘

Step 2: Reset Main
┌────────────────────────────────────────┐
│ $ git checkout main                    │
│ $ git reset --hard your-branch         │
│                                        │
│ main: old ────X───> new (your-branch) │
└────────────────────────────────────────┘

Step 3: Force Push
┌────────────────────────────────────────┐
│ $ git push -f origin main              │
│                                        │
│ ⚠️  Overwrites remote main             │
└────────────────────────────────────────┘
```

---

## Timeline View

```
Before Promotion:
───────────────────────────────────────────
Time ──────────────────────────────────>

main:          [doesn't exist yet]

your-branch:   A──B──C──D (current)
               └─────────┘
               clean subset
               

After Promotion:
───────────────────────────────────────────
Time ──────────────────────────────────>

main:          A──B──C──D (default)
               └─────────┘
               promoted!

your-branch:   [optional: keep or delete]
```

---

## Decision Tree

```
START: I want to promote my branch
│
├─ Is this a team project?
│  ├─ YES → Use Pull Request method
│  └─ NO → Continue
│
├─ Does main branch exist?
│  ├─ NO → Use Simple Create method
│  └─ YES → Continue
│
├─ Do I want to keep main's history?
│  ├─ YES → Use Merge method
│  └─ NO → Use Force Replace method
│
└─ Am I confident in my changes?
   ├─ YES → Proceed
   └─ NO → Create backup first
```

---

## What Each Method Preserves

```
┌─────────────┬─────────┬──────────┬─────────────┐
│   Method    │ History │ Commits  │ Reversible  │
├─────────────┼─────────┼──────────┼─────────────┤
│ Create New  │   ✓     │    ✓     │     ✓       │
│ Pull Req    │   ✓     │    ✓     │     ✓       │
│ Merge       │   ✓     │    ✓     │     ✓       │
│ Force Reset │   ✗     │  ✓ new   │  ✗ (backup) │
└─────────────┴─────────┴──────────┴─────────────┘
```

---

## Your Specific Case

```
Current Branch: copilot/promote-subset-clean-branch
Target: main (doesn't exist)
Content: Clean WordPress subset

Recommended: Simple Create Method
├─ Why: No existing main to conflict with
├─ Risk: Very low
├─ Steps: Just 3 commands + GitHub UI
└─ Time: < 5 minutes

Commands:
┌────────────────────────────────────────┐
│ git checkout -b main                   │
│ git push origin main                   │
│ (Then set as default in GitHub)        │
└────────────────────────────────────────┘
```

---

## Common Scenarios

### Scenario A: First Time Setup
```
Situation: Brand new repo, no main yet
Solution: Simple Create
Risk: None
```

### Scenario B: Team Project
```
Situation: Multiple contributors
Solution: Pull Request
Risk: Low (reviewed)
```

### Scenario C: Cleanup/Restart
```
Situation: Old main has issues
Solution: Force Replace (with backup)
Risk: Medium (make backup!)
```

### Scenario D: Adding Features
```
Situation: Main exists, adding to it
Solution: Merge or PR
Risk: Low
```

---

## Post-Promotion Checklist

```
After promoting to main, verify:

┌─ Verification Steps ─────────────────────┐
│ [ ] Main branch exists on GitHub         │
│ [ ] Main is set as default branch        │
│ [ ] All expected files are present       │
│ [ ] Can clone and checkout main          │
│ [ ] Old branch cleaned up (optional)     │
│ [ ] Team members notified (if team)      │
│ [ ] Branch protection set up (optional)  │
└───────────────────────────────────────────┘
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Create main from current | `git checkout -b main` |
| Push to remote | `git push origin main` |
| Delete old branch locally | `git branch -d old-branch` |
| Delete old branch remotely | `git push origin --delete old-branch` |
| Check current branch | `git branch` |
| View all branches | `git branch -a` |

---

For detailed instructions, see:
- **Quick Start:** [QUICK_START_PROMOTION.md](./QUICK_START_PROMOTION.md)
- **Full Guide:** [BRANCH_PROMOTION_GUIDE.md](./BRANCH_PROMOTION_GUIDE.md)
- **Repository Info:** [README.md](./README.md)
