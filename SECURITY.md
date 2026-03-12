# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**DO NOT** create public GitHub issues for security vulnerabilities.

### How to Report

1. **Email** repository owner privately (find email in GitHub profile)
2. **Include:**
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Status Updates**: Every 2 weeks until resolved
- **Fix Timeline**: 
  - Critical issues: 7-14 days
  - High severity: 30 days
  - Medium/Low: 60-90 days

### Disclosure Policy

- I'll work with you to understand and fix the issue
- Once fixed, I'll coordinate disclosure timing
- You'll be credited in the security advisory (if desired)

## Security Considerations

### What This App Does

Travel Shield creates a WiFi hotspot that routes traffic through your VPN. This involves:

- **Root privileges** - Required for iptables and network configuration
- **Network management** - Creates virtual interfaces and routing rules
- **Encrypted storage** - Uses system keyring for credentials

### Known Limitations

1. **Root Access Required**
   - App needs `sudo` for hostapd, dnsmasq, iptables
   - Review the code before granting permissions
   - We never store or transmit passwords

2. **Local Network Only**
   - Hotspot is for local device connection
   - No remote access or external services

3. **VPN Dependency**
   - Security depends on your VPN provider
   - App doesn't create VPN, only routes through it

### Best Practices

**For Users:**
- Review code before running with sudo
- Use strong hotspot passwords (12+ characters)
- Keep VPN connection active
- Use trusted VPN providers

**For Contributors:**
- Never hardcode credentials
- Sanitize all subprocess inputs
- Use parameterized commands (avoid shell injection)
- Validate user inputs (SSID, passwords)
- Log security-relevant events

### Out of Scope

The following are **not** considered vulnerabilities:

- Issues requiring physical access to the device
- Social engineering attacks
- DoS attacks on the local hotspot
- Theoretical attacks without proof-of-concept
- Issues in third-party dependencies (report to them)

## Security Tools

### Static Analysis

```bash
# Check for common issues
bandit -r src/

# Check dependencies
pip-audit
```

### Code Review Checklist

- [ ] No hardcoded secrets
- [ ] Subprocess calls use lists, not shell=True
- [ ] User inputs validated
- [ ] Errors don't expose sensitive info
- [ ] Temporary files cleaned up
- [ ] Network interfaces validated

## Credit

I appreciate responsible disclosure and will credit security researchers who:
- Report valid vulnerabilities
- Allow reasonable time to fix
- Don't disclose publicly before fix

Thank you for helping keep Travel Shield secure! 🔒
