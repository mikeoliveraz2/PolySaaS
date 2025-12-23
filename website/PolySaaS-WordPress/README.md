# PolySaaS WordPress SFTP Configuration

This directory contains SFTP configuration templates for managing WordPress deployments using VSCode's SFTP extension.

## Setup Instructions

1. Copy the `sftp.json.template` file in each environment directory to `sftp.json`
2. Replace the placeholder values with your actual credentials:
   - `YOUR_HOST_HERE` - Your Hostinger server IP or hostname
   - `YOUR_USERNAME_HERE` - Your SFTP username
   - `YOUR_PASSWORD_HERE` - Your SFTP password
   - `YOUR_DOMAIN_HERE` - Your domain name

3. **IMPORTANT**: Never commit the actual `sftp.json` files to git. They are already in `.gitignore`

## Security Note

The `sftp.json` files contain sensitive credentials and must NEVER be committed to version control. Always use the template files as a reference.

## Environments

- **site-sandbox/**: Sandbox environment configuration
- **site-staging/**: Staging environment configuration
