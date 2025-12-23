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

### Promoting Branches to Main

If you need to promote your current branch to main (or set up main for the first time), see the comprehensive guide:

📖 **[Branch Promotion Guide](./BRANCH_PROMOTION_GUIDE.md)**

This guide covers:
- Creating main from a clean subset branch
- Replacing existing main branch
- Using Pull Requests for safe promotion
- Post-promotion verification steps
- Troubleshooting common issues

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

## Additional Documentation

- [Branch Promotion Guide](./BRANCH_PROMOTION_GUIDE.md) - How to promote branches to main
- [WordPress Setup Guide](./website/setup%20vscode%20for%20wordpress.md) - VSCode + SFTP setup

## Support

For questions or issues, please open a GitHub issue in this repository.

---

**Note:** This is a working repository. Some structure and documentation may evolve as the project develops.
