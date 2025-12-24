# Branch Promotion Guide

## Overview

This guide describes the process for promoting code changes through different environments using Git branches.

## Branch Hierarchy

```
main (production)
  ↑
staging
  ↑
develop
  ↑
feature branches
```

## Workflow

### 1. Feature Development

Create a feature branch from `develop`:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/new-feature
```

Develop your feature, commit changes:

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 2. Code Review

1. Create Pull Request to `develop`
2. Request reviews from team members
3. Address feedback
4. Get approval

### 3. Merge to Develop

After approval:

```bash
# On GitHub, merge PR to develop
# Or via command line:
git checkout develop
git merge --no-ff feature/new-feature
git push origin develop
```

### 4. Testing in Development

- Automated tests run on `develop`
- Manual testing performed
- QA validation

### 5. Promote to Staging

When ready for staging:

```bash
git checkout staging
git pull origin staging
git merge --no-ff develop
git push origin staging
```

### 6. Staging Validation

- Deploy to staging environment
- Perform UAT (User Acceptance Testing)
- Validate integrations
- Performance testing

### 7. Promote to Production

After successful staging validation:

```bash
git checkout main
git pull origin main
git merge --no-ff staging
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags
```

## Branch Protection Rules

### Main Branch
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date
- Include administrators
- No force pushes
- No deletions

### Staging Branch
- Require pull request reviews (optional)
- Require status checks to pass
- No force pushes

### Develop Branch
- Require status checks to pass
- No force pushes

## Hotfix Process

For urgent production fixes:

```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug

# Fix the issue
git add .
git commit -m "fix: resolve critical bug"

# Merge to main
git checkout main
git merge --no-ff hotfix/critical-bug
git tag -a v1.0.1 -m "Hotfix release 1.0.1"
git push origin main --tags

# Also merge to staging and develop
git checkout staging
git merge --no-ff hotfix/critical-bug
git push origin staging

git checkout develop
git merge --no-ff hotfix/critical-bug
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-bug
git push origin --delete hotfix/critical-bug
```

## Release Process

### Prepare Release

```bash
git checkout develop
git checkout -b release/v1.0.0

# Update version numbers
# Update CHANGELOG.md
# Final testing

git add .
git commit -m "chore: prepare release v1.0.0"
```

### Finalize Release

```bash
# Merge to main
git checkout main
git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0"

# Merge back to develop
git checkout develop
git merge --no-ff release/v1.0.0

# Push everything
git push origin main --tags
git push origin develop

# Delete release branch
git branch -d release/v1.0.0
```

## Continuous Integration

### Automated Checks

Each environment triggers:

**On feature branches:**
- Linting
- Unit tests
- Code coverage

**On develop:**
- All feature checks
- Integration tests
- Build verification

**On staging:**
- All develop checks
- E2E tests
- Security scans
- Performance tests

**On main:**
- All staging checks
- Deployment to production
- Smoke tests
- Monitoring alerts

## Best Practices

### Commit Messages

Follow conventional commits:

```
feat: add user authentication
fix: resolve login button issue
docs: update API documentation
style: format code with prettier
refactor: simplify user service
test: add tests for auth module
chore: update dependencies
```

### Pull Request Guidelines

1. **Title**: Clear, descriptive
2. **Description**: What, why, how
3. **Screenshots**: For UI changes
4. **Tests**: Include test results
5. **Documentation**: Update if needed

### Merge Strategy

- **Feature to Develop**: Squash and merge (clean history)
- **Develop to Staging**: Merge commit (track integration)
- **Staging to Main**: Merge commit (track releases)
- **Hotfix**: Merge commit (track fixes)

## Rollback Procedure

If issues are found in production:

### Quick Rollback

```bash
git checkout main
git revert HEAD
git push origin main
```

### Rollback to Specific Version

```bash
git checkout main
git reset --hard v1.0.0
git push origin main --force  # Use with caution!
```

### Rollback with New Commit

```bash
git checkout main
git revert <commit-hash>
git push origin main
```

## Environment Variables

Manage environment-specific config:

- **Development**: `.env.development`
- **Staging**: `.env.staging`
- **Production**: `.env.production`

Never commit these files! Use `.env.example` as template.

## Monitoring

After promotion to each environment:

1. Check application logs
2. Monitor error rates
3. Verify metrics (response time, throughput)
4. Check resource usage
5. Validate integrations

## Checklist

### Before Merging to Develop
- [ ] Code reviewed and approved
- [ ] All tests passing
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Changelog updated

### Before Promoting to Staging
- [ ] All develop tests passing
- [ ] Integration tests verified
- [ ] No critical bugs
- [ ] Stakeholder approval

### Before Promoting to Main
- [ ] Staging tests passing
- [ ] UAT completed successfully
- [ ] Performance validated
- [ ] Security scan clear
- [ ] Rollback plan ready
- [ ] Team notified
- [ ] Monitoring ready

## Troubleshooting

### Merge Conflicts

```bash
# Start merge
git merge feature-branch

# If conflicts occur
git status  # See conflicted files

# Edit files to resolve conflicts
# Then:
git add resolved-file
git commit
```

### Failed CI/CD

1. Check CI/CD logs
2. Reproduce locally
3. Fix issues
4. Push fixes
5. Wait for CI/CD to pass

### Emergency Stop

If deployment must be stopped:

1. Contact DevOps team
2. Stop deployment pipeline
3. Assess situation
4. Rollback if necessary
5. Document incident

## Additional Resources

- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
