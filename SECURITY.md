# Security Policy

## 🔒 Current Security Issues

### Critical: Exposed Credentials

This repository currently contains exposed credentials that should be addressed immediately:

1. **API Keys in Source Code** (`rag_agent.py`, line 22)
   - An API key is visible in the source code
   - **Action Required**: Remove and rotate this key immediately

2. **Credentials in Plain Text** (`txt` file)
   - Username and password stored in plain text
   - API keys stored without encryption
   - **Action Required**: Remove this file from version control

3. **Git History Contamination**
   - Credentials may exist in git history
   - **Action Required**: Consider using tools like `git-filter-repo` or BFG Repo-Cleaner

## ✅ Recommended Security Practices

### 1. Environment Variables
Store sensitive data in environment variables instead of source code:

```python
# Bad
api_key = "dfdfdfdfdfdf99erefddfd"

# Good
import os
api_key = os.getenv("OPENROUTER_API_KEY")
```

### 2. Use .env Files (Never Commit)
Create a `.env` file for local development:

```bash
OPENROUTER_API_KEY=your_key_here
USERNAME=your_username
PASSWORD=your_password
```

Load it with python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()
```

### 3. Provide .env.example
Create a template without real values:

```bash
# .env.example
OPENROUTER_API_KEY=your_api_key_here
USERNAME=your_username_here
PASSWORD=your_password_here
```

### 4. Update .gitignore
Ensure sensitive files are never committed:
- `.env`
- `txt` (credential file)
- `*.key`
- `*.pem`

### 5. Rotate Compromised Credentials
All exposed credentials should be:
- Immediately revoked/rotated
- Updated in secure storage
- Never reused

### 6. Use Secrets Management
For production, consider:
- GitHub Secrets (for CI/CD)
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Environment-specific configuration management

## 🐛 Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do NOT** open a public issue
2. Contact the repository owner directly
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

## 📋 Security Checklist for Contributors

Before contributing, ensure:
- [ ] No credentials in code
- [ ] No credentials in commit messages
- [ ] Sensitive files in .gitignore
- [ ] Using environment variables for configuration
- [ ] No hardcoded passwords or API keys
- [ ] Dependencies are up to date
- [ ] No known vulnerable packages

## 🔄 Immediate Actions Required

1. **Remove exposed credentials** from:
   - `rag_agent.py` (line 22)
   - `txt` file
   
2. **Add to .gitignore**:
   - `txt`
   - `.env`
   
3. **Rotate all exposed credentials**:
   - OpenRouter API key
   - Any usernames/passwords
   
4. **Clean git history** (optional but recommended):
   ```bash
   # Use git-filter-repo to remove sensitive files from history
   git filter-repo --path txt --invert-paths
   ```

5. **Update code** to use environment variables:
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   api_key = os.getenv("OPENROUTER_API_KEY")
   ```

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Last Updated**: 2025-11-20
