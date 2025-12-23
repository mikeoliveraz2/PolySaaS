# PolySaaS

A WordPress-based SaaS platform with custom themes and configurations for multiple environments.

## Overview

PolySaaS is a WordPress project that includes custom child themes and configurations for managing a SaaS website. The project supports multiple environments (staging and sandbox) for development and testing.

## Structure

```
website/
├── PolySaaS-WordPress/     # SFTP configuration files
│   ├── site-sandbox/
│   └── site-staging/
├── sandbox/                # Sandbox environment
│   ├── index.php
│   ├── wp-config.php       (empty - configured on server)
│   └── wp-content/
│       └── themes/
│           └── polysaas-pro/
├── staging/                # Staging environment
│   ├── index.php
│   ├── wp-config.php       (empty - configured on server)
│   └── wp-content/
│       └── themes/
│           └── polysaas-pro/
└── setup vscode for wordpress.md
```

## Environments

- **Sandbox**: darkgreen-armadillo-734129.hostingersite.com
- **Staging**: azure-nightingale-589250.hostingersite.com

## Theme: PolySaaS Pro

A custom child theme based on Twenty Twenty-Five, providing:
- Full control over customizations
- Upgrade-safe modifications
- Custom styling and functionality

### Theme Files

- `functions.php` - Custom WordPress functions and hooks
- `style.css` - Theme stylesheet with metadata

## Development Setup

### Prerequisites

- VSCode with SFTP extension
- Access to Hostinger SFTP credentials
- PHP 7.4+ (for local syntax checking)

### SFTP Setup

See `website/setup vscode for wordpress.md` for detailed instructions on:
- Installing the SFTP extension
- Configuring SFTP credentials
- Syncing files with the server
- Live editing workflow

## Security

- `wp-config.php` files are empty in the repository (credentials configured on server only)
- SFTP credentials are gitignored
- Uploads directory excluded from version control

## Contributing

When making changes:
1. Use the appropriate environment (sandbox for testing, staging for review)
2. Test changes before deploying to production
3. Keep theme files organized and documented

## License

Proprietary - PolySaaS Team
