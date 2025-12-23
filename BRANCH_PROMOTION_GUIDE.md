# Branch Promotion Guide: Subset Clean to Main

This guide explains how to promote the `subset-clean` branch (or current working branch) to become the main branch of the PolySaaS repository.

## Current Situation

You have a branch containing a clean subset of your WordPress site (excluding uploads and .wpress files) that you want to make the primary/main branch of the repository.

## Prerequisites

Before proceeding, ensure:
- ✅ Your current branch contains all the files you want in main
- ✅ All changes are committed and pushed
- ✅ You have admin access to the GitHub repository
- ✅ You've backed up any important data from the existing main branch (if it exists)

## Method 1: Create Main Branch from Current Branch (Recommended if main doesn't exist)

If there's no main branch yet, this is the simplest approach:

```bash
# 1. Make sure you're on your clean subset branch
git checkout copilot/promote-subset-clean-branch

# 2. Create a new main branch from current branch
git branch main

# 3. Switch to main branch
git checkout main

# 4. Push main branch to remote
git push origin main

# 5. Set main as the default branch in GitHub
# Go to: Settings → Branches → Default branch → Switch to 'main'
```

## Method 2: Replace Existing Main Branch (If main already exists)

If a main branch already exists but you want to replace it with your clean subset:

### Option A: Hard Reset (Complete Replacement)

**⚠️ WARNING: This permanently replaces main branch history**

```bash
# 1. Make sure you're on your clean subset branch
git checkout copilot/promote-subset-clean-branch

# 2. Create backup of current main (safety precaution)
git branch main-backup-$(date +%Y%m%d-%H%M%S)
git push origin main-backup-$(date +%Y%m%d-%H%M%S)

# 3. Delete your local main branch
git branch -D main

# 4. Create new main from your current branch
git checkout -b main

# 5. Force push to replace remote main
git push -f origin main
```

### Option B: Merge Strategy (Preserves History)

```bash
# 1. Switch to main branch
git checkout main

# 2. Merge your clean subset branch
git merge copilot/promote-subset-clean-branch

# 3. Push changes
git push origin main
```

### Option C: Pull Request Method (Safest, Recommended for Teams)

This is the safest method and allows for review:

1. **Create a Pull Request on GitHub:**
   - Go to your repository on GitHub
   - Navigate to the Pull Requests section
   - Click "New Pull Request"
   - Set base: `main`, compare: `copilot/promote-subset-clean-branch`
   - Review the changes
   - Create the pull request

2. **Review and Merge:**
   - Review all changes in the PR
   - If everything looks good, click "Merge Pull Request"
   - Choose merge strategy:
     - "Create a merge commit" - preserves all history
     - "Squash and merge" - combines all commits into one
     - "Rebase and merge" - applies commits on top of main

3. **Delete the old branch (optional):**
   ```bash
   git branch -d copilot/promote-subset-clean-branch
   git push origin --delete copilot/promote-subset-clean-branch
   ```

## Method 3: Rename Current Branch to Main

If you want to simply rename your current branch:

```bash
# 1. Rename your local branch
git branch -m copilot/promote-subset-clean-branch main

# 2. Push and set upstream
git push origin main

# 3. Delete old remote branch
git push origin --delete copilot/promote-subset-clean-branch

# 4. Set main as default in GitHub settings
```

## Post-Promotion Steps

After promoting to main:

1. **Set Main as Default Branch in GitHub:**
   - Go to: Repository Settings → Branches
   - Under "Default branch", click the switch icon
   - Select `main` from dropdown
   - Click "Update"

2. **Update Local Repository:**
   ```bash
   git checkout main
   git pull origin main
   ```

3. **Update Branch Protection Rules (Recommended):**
   - Go to: Repository Settings → Branches
   - Add rule for `main` branch
   - Enable:
     - ✅ Require pull request reviews before merging
     - ✅ Require status checks to pass
     - ✅ Include administrators (optional)

4. **Clean Up Old Branches:**
   ```bash
   # List all branches
   git branch -a
   
   # Delete local branches you no longer need
   git branch -d old-branch-name
   
   # Delete remote branches
   git push origin --delete old-branch-name
   ```

## Verification Steps

After promotion, verify everything worked:

```bash
# Check current branch
git branch

# View commit history
git log --oneline -10

# Check remote branches
git branch -r

# Verify remote tracking
git remote show origin
```

## Troubleshooting

### Issue: "failed to push some refs"
**Solution:** Use `git push -f origin main` (only if you're sure you want to overwrite)

### Issue: "Permission denied"
**Solution:** Ensure you have write access to the repository

### Issue: "Branch protection rules"
**Solution:** Temporarily disable branch protection in Settings → Branches

### Issue: "Merge conflicts"
**Solution:** Resolve conflicts manually:
```bash
git merge copilot/promote-subset-clean-branch
# Fix conflicts in files
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

## Best Practices

1. **Always backup before major branch operations**
2. **Use Pull Requests for team projects**
3. **Test in a staging environment first**
4. **Communicate with team members before changing default branch**
5. **Document what's included/excluded from the clean subset**
6. **Set up branch protection rules on main**

## Quick Reference

For the most common scenario (promoting current branch to main):

```bash
# If main doesn't exist yet:
git checkout -b main
git push origin main

# If main exists and you want to replace it:
git checkout main
git reset --hard copilot/promote-subset-clean-branch
git push -f origin main

# Via Pull Request (safest):
# Use GitHub UI to create PR from your branch to main, then merge
```

## Additional Resources

- [GitHub: About branches](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches)
- [GitHub: Changing the default branch](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/changing-the-default-branch)
- [Git: Branch Management](https://git-scm.com/book/en/v2/Git-Branching-Branch-Management)

---

**Need Help?** If you're unsure which method to use, start with Method 3 (Pull Request) as it's the safest and most reversible.
