# Development Guide

## Setting Up Development Environment

### 1. Clone and Setup

```bash
git clone https://github.com/DrenVive/travel_router.git
cd travel_router

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## Project Structure

```
travel_router/
├── src/                    # Main source code
│   ├── __init__.py        # Package initialization
│   ├── core/              # Core functionality
│   │   └── __init__.py    # Logging, config, D-Bus setup
│   ├── network/           # Network management
│   │   ├── __init__.py    # Module exports
│   │   ├── detector.py    # VPN/WiFi detection
│   │   ├── hotspot.py     # Hotspot creation
│   │   └── routing.py     # IP routing & iptables
│   ├── ui/                # User interface
│   │   ├── __init__.py    # Module exports
│   │   └── app.py         # GTK4 application
│   └── utils/             # Utilities
│       ├── __init__.py    # Module exports
│       └── config.py      # Encrypted config storage
├── scripts/               # Helper scripts
│   ├── diagnose.sh        # System diagnostics
│   ├── test_concurrent_ap.sh  # AP testing
│   └── create_concurrent_ap.sh  # Manual AP creation
├── docs/                  # Documentation
│   ├── API.md            # API documentation
│   └── DEVELOPMENT.md    # This file
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # User documentation
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Imports**: Group by stdlib, third-party, local
- **Docstrings**: Google style

Example:

```python
"""Module docstring.

Detailed description of what this module does.
"""

import os
import sys

import NetworkManager
from gi.repository import Gtk

from src.core import logger


class MyClass:
    """Brief class description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    """
    
    def my_method(self, arg1, arg2):
        """Brief method description.
        
        Args:
            arg1: Description
            arg2: Description
            
        Returns:
            Description of return value
            
        Raises:
            ValueError: When something is wrong
        """
        pass
```

### Logging

Use the centralized logger:

```python
from src.core import logger

logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)  # Include traceback
```

### Error Handling

Always provide context in exceptions:

```python
try:
    result = subprocess.run(cmd, check=True, capture_output=True)
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {' '.join(cmd)}", exc_info=True)
    raise Exception(f"Failed to execute {cmd[0]}: {e.stderr.decode()}")
```

## Adding New Features

### 1. Network Detection Enhancement

To add detection for a new VPN type:

**File**: `src/network/detector.py`

```python
def check_vpn_status(self):
    """Check for active VPN connection"""
    # ... existing code ...
    
    # Add new VPN type
    if conn.Type in ['vpn', 'wireguard', 'tun', 'your_vpn_type']:
        self.vpn_connection = conn
        logger.info(f"VPN connection found: {conn.Id}")
        return True
```

### 2. New Hotspot Configuration

To add new hostapd options:

**File**: `src/network/hotspot.py`

```python
def _start_hostapd(self, ap_iface, ssid, password, hw_mode, channel):
    """Start hostapd daemon"""
    hostapd_conf = f"""interface={ap_iface}
driver=nl80211
# ... existing config ...
# Add your new options here
wmm_enabled=1
uapsd_advertisement_enabled=1
"""
```

### 3. UI Enhancements

To add new GUI elements:

**File**: `src/ui/app.py`

```python
def _build_ui(self, win):
    """Build the user interface"""
    # ... existing code ...
    
    # Add new section
    self._add_advanced_options(box)

def _add_advanced_options(self, parent_box):
    """Add advanced options section"""
    frame = Gtk.Frame()
    # Build your UI components
    parent_box.append(frame)
```

## Testing

### Manual Testing

```bash
# Run with debug output
python3 main.py 2>&1 | tee debug_output.log

# Check logs
tail -f travel_router_debug.log

# Monitor network interfaces
watch -n 1 'ip addr show'

# Check iptables rules
sudo iptables -L -n -v
sudo iptables -t nat -L -n -v
```

### Testing Network Components

```python
# Create test script: test_network.py
from src.network import NetworkDetector

detector = NetworkDetector()
print(f"VPN: {detector.check_vpn_status()}")
print(f"WiFi: {detector.check_wifi_device()}")
if detector.wifi_device:
    print(f"Interface: {detector.wifi_device.Interface}")
```

Run it:
```bash
python3 test_network.py
```

### Testing Hotspot Creation

```bash
# Use the test script
bash scripts/test_concurrent_ap.sh
```

## Debugging

### Common Issues

#### "Import gi could not be resolved"

This is a false positive from Pylance. The code works fine because `gi` is a system package. To suppress:

1. Install `python3-gi` system package
2. Add to VS Code settings: `"python.analysis.ignore": ["gi"]`

#### D-Bus Connection Errors

Make sure D-Bus is initialized:

```python
from src.core import initialize_dbus
initialize_dbus()  # Call this BEFORE any NetworkManager operations
```

#### Hotspot Won't Start

Check logs in order:
1. `travel_router_debug.log` - Application logs
2. `/tmp/hostapd.log` - hostapd daemon logs
3. `/tmp/dnsmasq.log` - DHCP server logs
4. `journalctl -u NetworkManager` - NetworkManager logs

### Debug Mode

Enable verbose logging:

```python
# In src/core/__init__.py
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detail
    # ... rest of config
)
```

## Making a Release

### 1. Update Version

Edit `src/__init__.py`:

```python
__version__ = "1.1.0"  # Bump version
```

### 2. Update CHANGELOG

Create `CHANGELOG.md` if not exists:

```markdown
## [1.1.0] - 2026-03-12

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Change description
```

### 3. Tag Release

```bash
git add .
git commit -m "Release v1.1.0"
git tag -a v1.1.0 -m "Version 1.1.0"
git push origin main --tags
```

### 4. Create GitHub Release

Go to GitHub → Releases → Create new release

## Contributing

### Pull Request Process

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** following coding standards
4. **Test thoroughly**
5. **Commit**: `git commit -m "Add amazing feature"`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open Pull Request** with description

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(network): add support for OpenVPN detection

- Add OpenVPN to VPN type detection
- Update tests for new VPN type
- Add logging for OpenVPN connections

Closes #123
```

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
detector.check_vpn_status()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 slowest functions
```

### Memory Monitoring

```bash
# Monitor memory usage
watch -n 1 'ps aux | grep python3 | grep main.py'
```

## Troubleshooting Development Issues

### Virtual Environment Issues

```bash
# Recreate venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### GTK Import Issues

```bash
# Install GTK dependencies
sudo apt install python3-gi gir1.2-gtk-4.0

# Test GTK import
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('OK')"
```

### NetworkManager Issues

```bash
# Check NetworkManager status
systemctl status NetworkManager

# Restart if needed
sudo systemctl restart NetworkManager
```

## Resources

- [GTK 4 Documentation](https://docs.gtk.org/gtk4/)
- [NetworkManager D-Bus API](https://networkmanager.dev/docs/api/latest/)
- [hostapd Documentation](https://w1.fi/hostapd/)
- [Python Style Guide (PEP 8)](https://pep8.org/)
