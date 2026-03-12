# Contributing to Travel Shield

First off, thanks for taking the time to contribute! 🎉

### Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

## How to Contribute

### Reporting Bugs

**Before submitting a bug report:**
- Check if the issue has already been reported
- Collect logs: `travel_router_debug.log`, `/tmp/hostapd.log`

**Good bug report includes:**
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- System info (OS, Python version)
- Relevant logs

### Suggesting Features

**Feature requests should:**
- Explain the problem you're trying to solve
- Describe the solution you'd like
- Consider alternatives you've thought about

### Pull Requests

1. **Fork & Create Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Follow Code Style**
   - PEP 8 compliance
   - 100 character line limit
   - Docstrings for functions/classes
   - Type hints where appropriate

3. **Test Your Changes**
   ```bash
   python3 main.py  # Ensure it runs
   # Test hotspot creation
   # Check logs for errors
   ```

4. **Commit Messages**
   ```
   type(scope): brief description
   
   Longer explanation if needed
   ```
   
   Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

5. **Submit PR**
   - Reference related issues
   - Describe what changed and why
   - Include screenshots for UI changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/travel_router.git
cd travel_router

# Setup environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make changes
# ...

# Test
python3 main.py
```

## Code Review Process

- Maintainers review PRs within 1-2 weeks
- Address feedback by pushing to your branch
- Once approved, maintainer will merge

## Security

**DO NOT** create public issues for security vulnerabilities.

Instead, email security concerns to the repository owner with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

## License

By contributing, you agree your contributions will be licensed under the MIT License.

## Questions?

Feel free to open a discussion or issue for any questions!

---

Thank you for contributing! 🙏
