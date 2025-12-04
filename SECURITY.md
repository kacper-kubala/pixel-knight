# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **Do NOT** open a public issue
2. Email the maintainers directly (or use GitHub's private vulnerability reporting)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to understand and address the issue.

## Security Best Practices

When using Pixel Knight:

- **API Keys**: Never commit API keys to the repository. Use `.env` files (gitignored)
- **Database**: Use strong passwords for PostgreSQL/Supabase
- **Network**: If exposing to the internet, use HTTPS and proper authentication
- **Updates**: Keep dependencies updated (`pip install -U -r requirements.txt`)

