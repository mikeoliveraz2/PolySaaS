# PolySaaS

A full-stack SaaS platform combining WordPress and modern web technologies.

## Repository Structure

```
PolySaaS/
├── website/              # WordPress-related files and configurations
│   ├── PolySaaS-WordPress/    # WordPress site files
│   ├── sandbox/               # Testing environment
│   ├── staging/               # Staging environment
│   └── setup vscode for wordpress.md  # Development setup guide
└── BRANCH_PROMOTION_GUIDE.md  # Guide for managing branch promotions
```

## Getting Started

### WordPress Development Setup

See [setup vscode for wordpress.md](./website/setup%20vscode%20for%20wordpress.md) for instructions on setting up your development environment with VSCode and SFTP.

### Staging Sites

- **Primary Staging:** azure-nightingale-589250.hostingersite.com
- **Sandbox:** darkgreen-armadillo-734129.hostingersite.com

## Branch Management

This repository uses a clean subset approach, excluding large files like uploads and .wpress archives.

### 🚀 Promoting Your Branch to Main

**Quick Answer:** Need to promote your subset-clean branch to main? Start here:

1. **⚡ Quick Start** → [QUICK_START_PROMOTION.md](./QUICK_START_PROMOTION.md) - Get it done in 5 minutes
2. **📖 Full Guide** → [BRANCH_PROMOTION_GUIDE.md](./BRANCH_PROMOTION_GUIDE.md) - Complete reference with all methods
3. **📊 Visual Guide** → [WORKFLOW_DIAGRAM.md](./WORKFLOW_DIAGRAM.md) - Flowcharts and diagrams

**What you'll learn:**
- ✅ How to create main branch from your clean subset
- ✅ Multiple promotion methods (simple, merge, force, PR)
- ✅ Step-by-step instructions for your specific situation
- ✅ Safety checks and troubleshooting
- ✅ Post-promotion verification steps

## Development Workflow

1. **Make changes** in your development environment
2. **Commit changes** to your feature branch
3. **Test** on staging site
4. **Create Pull Request** to merge into main
5. **Review and merge** after testing

## Project Status

This repository contains a clean subset of the WordPress site, excluding:
- Upload directories (large media files)
- `.wpress` backup files
- Other large binary files

This keeps the repository lightweight and focused on source code.

## Contributing

When contributing to this repository:

1. Create a feature branch from main
2. Make your changes
3. Test thoroughly on staging
4. Submit a Pull Request
5. Wait for review and approval

## Documentation Index

### Branch Management
- 📋 [Quick Start: Promote to Main](./QUICK_START_PROMOTION.md) - Fast 5-minute guide
- 📖 [Complete Branch Promotion Guide](./BRANCH_PROMOTION_GUIDE.md) - Full reference
- 📊 [Workflow Diagrams](./WORKFLOW_DIAGRAM.md) - Visual flowcharts and decision trees

### Development Setup
- 🔧 [WordPress Setup Guide](./website/setup%20vscode%20for%20wordpress.md) - VSCode + SFTP configuration

## Support

For questions or issues, please open a GitHub issue in this repository.

---

**Note:** This is a working repository. Some structure and documentation may evolve as the project develops.
