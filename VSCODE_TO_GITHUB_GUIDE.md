# VS Code to GitHub Import Guide

## Overview

This guide explains how to import a local VS Code project to GitHub, particularly useful for existing projects that need to be version-controlled.

## Prerequisites

- Git installed on your system
- GitHub account
- VS Code with Git integration
- GitHub CLI (optional but recommended)

## Step-by-Step Guide

### 1. Initialize Git Repository

If your project doesn't have Git initialized:

```bash
cd your-project-directory
git init
```

### 2. Create .gitignore

Create a `.gitignore` file to exclude unnecessary files:

```
# Dependencies
node_modules/
venv/
__pycache__/

# IDE
.vscode/sftp.json
.idea/

# Environment
.env
.env.local

# Build artifacts
dist/
build/
*.log
```

### 3. Stage and Commit Files

```bash
git add .
git commit -m "Initial commit"
```

### 4. Create GitHub Repository

#### Option A: Using GitHub CLI
```bash
gh repo create your-repo-name --public --source=. --remote=origin
git push -u origin main
```

#### Option B: Using GitHub Web Interface

1. Go to https://github.com/new
2. Create a new repository
3. Don't initialize with README (since you have local files)
4. Copy the repository URL

### 5. Add Remote and Push

```bash
git remote add origin https://github.com/username/repo-name.git
git branch -M main
git push -u origin main
```

## VS Code Integration

### Install GitHub Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "GitHub Pull Requests and Issues"
4. Install and authenticate

### Using Source Control

1. Open Source Control panel (Ctrl+Shift+G)
2. Stage changes by clicking '+'
3. Enter commit message
4. Click checkmark to commit
5. Click '...' → Push to push changes

## Common Issues

### Large Files

If you have large files:

```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.psd"
git lfs track "*.zip"

# Add .gitattributes
git add .gitattributes
```

### Authentication Issues

Use Personal Access Token for HTTPS:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Use token as password when pushing

Or use SSH:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add key to GitHub: Settings → SSH and GPG keys
git remote set-url origin git@github.com:username/repo.git
```

### Existing Remote

If remote already exists:
```bash
git remote remove origin
git remote add origin new-url
```

## Best Practices

1. **Commit Often**: Make small, focused commits
2. **Write Good Messages**: Describe what and why, not how
3. **Use Branches**: Don't commit directly to main for features
4. **Review Changes**: Always review staged changes before committing
5. **Pull Before Push**: Avoid conflicts by pulling latest changes

## Branch Strategy

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push branch
git push -u origin feature/new-feature

# Create pull request on GitHub
# Merge after review
```

## Useful Commands

```bash
# Check status
git status

# View changes
git diff

# View history
git log --oneline --graph

# Undo unstaged changes
git checkout -- filename

# Undo last commit (keep changes)
git reset HEAD~1

# View remote
git remote -v
```

## For WordPress Projects

Special considerations for WordPress:

```
# .gitignore for WordPress
wp-content/uploads/
wp-content/cache/
wp-content/backup-db/
wp-config.php
.htaccess
*.log
```

## Security Checklist

Before pushing to GitHub:

- [ ] No passwords or API keys in code
- [ ] No database credentials
- [ ] No SFTP/FTP passwords
- [ ] `.env` file in `.gitignore`
- [ ] `wp-config.php` excluded (for WordPress)
- [ ] SSL certificates excluded
- [ ] Private keys excluded

## Troubleshooting

### Push Rejected

```bash
# If remote has changes you don't have
git pull origin main --rebase
git push origin main
```

### Wrong Files Committed

```bash
# Remove from Git but keep locally
git rm --cached filename

# Remove from history (use carefully)
git filter-branch --tree-filter 'rm -f filename' HEAD
```

## Resources

- [GitHub Docs](https://docs.github.com/)
- [Git Documentation](https://git-scm.com/doc)
- [VS Code Git Integration](https://code.visualstudio.com/docs/editor/versioncontrol)

## Next Steps

After importing:
1. Set up branch protection rules
2. Configure GitHub Actions for CI/CD
3. Set up issue templates
4. Add collaborators
5. Configure repository settings
