# Quick Start: Branch Promotion

Quick reference guide for promoting code through environments.

## One-Command Promotions

### Feature → Develop
```bash
git checkout develop && git pull && git merge --no-ff feature/your-feature && git push
```

### Develop → Staging
```bash
git checkout staging && git pull && git merge --no-ff develop && git push
```

### Staging → Production
```bash
git checkout main && git pull && git merge --no-ff staging && git tag -a v1.0.0 -m "Release 1.0.0" && git push --follow-tags
```

## Pre-Flight Checks

### Before ANY Promotion
```bash
# Ensure you're up to date
git pull origin $(git branch --show-current)

# Check for uncommitted changes
git status

# Verify tests pass
make test  # or npm test, pytest, etc.
```

## Emergency Hotfix

```bash
# From main
git checkout main
git checkout -b hotfix/issue-description
# ... make fix ...
git checkout main && git merge --no-ff hotfix/issue-description
git checkout staging && git merge --no-ff hotfix/issue-description
git checkout develop && git merge --no-ff hotfix/issue-description
git push origin main staging develop
```

## Rollback

### Quick revert last commit
```bash
git checkout main
git revert HEAD
git push origin main
```

### Rollback to tag
```bash
git checkout main
git reset --hard v1.0.0
git push origin main --force  # ⚠️  Use with caution
```

## Common Commands

```bash
# View branches
git branch -a

# View tags
git tag -l

# Compare branches
git diff develop..staging

# View commit history
git log --oneline --graph --all

# Check which branch contains a commit
git branch --contains <commit-hash>
```

## Workflow Diagram

```
┌──────────────┐
│   Feature    │──┐
│   Branches   │  │
└──────────────┘  │
                  ├──> ┌──────────┐
┌──────────────┐  │    │ Develop  │──> Tests, Integration
│   Feature    │──┘    └──────────┘
│   Branches   │           │
└──────────────┘           │
                           ▼
                    ┌──────────┐
                    │ Staging  │──> UAT, Performance
                    └──────────┘
                           │
                           ▼
                    ┌──────────┐
                    │   Main   │──> Production
                    └──────────┘
```

## Status Checks

### Before Merging to Main

- [ ] All CI/CD checks pass
- [ ] Code review approved
- [ ] Staging tests successful
- [ ] UAT completed
- [ ] Security scan clear
- [ ] Performance metrics acceptable
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Team notified

## Troubleshooting

### Merge Conflict
```bash
# See conflicts
git status

# Abort merge
git merge --abort

# Or resolve and continue
# Edit conflicted files, then:
git add <resolved-files>
git commit
```

### Wrong Branch Merged
```bash
# Undo merge (if not pushed)
git reset --hard HEAD~1

# If already pushed, revert
git revert -m 1 <merge-commit-hash>
```

### CI/CD Failing
1. Check logs in GitHub Actions/CI system
2. Reproduce issue locally
3. Fix and push
4. Wait for new CI/CD run

## Best Practices

1. **Always Pull First**: `git pull` before merging
2. **Use --no-ff**: Preserves merge history
3. **Tag Releases**: Makes rollback easier
4. **Test Locally**: Don't rely only on CI/CD
5. **Communicate**: Let team know about promotions

## Environment-Specific Tasks

### After Deploying to Develop
- Run integration tests
- Check feature flags
- Verify database migrations

### After Deploying to Staging
- Perform UAT
- Load testing
- Security scan
- Cross-browser testing

### After Deploying to Production
- Monitor error rates
- Check performance metrics
- Verify critical user paths
- Watch for alerts

## Quick References

### Semantic Versioning
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes

### Conventional Commits
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructure
- `test:` Tests
- `chore:` Maintenance

## Need More Details?

See [BRANCH_PROMOTION_GUIDE.md](BRANCH_PROMOTION_GUIDE.md) for comprehensive documentation.
