# API Documentation

## Core Module (`src/core/`)

### Configuration

```python
from src.core import logger, initialize_dbus, APP_NAME, APP_ID

# Application constants
APP_NAME = "Travel Shield"
APP_ID = "com.travelrouter.app"
LOG_FILE = "travel_router_debug.log"

# Initialize D-Bus (call once at startup)
initialize_dbus()

# Use the logger
logger.info("Application started")
logger.error("Something went wrong", exc_info=True)
```

## Network Module (`src/network/`)

### NetworkDetector

Detects VPN connections and WiFi devices.

```python
from src.network import NetworkDetector

detector = NetworkDetector()

# Check VPN status
if detector.check_vpn_status():
    print(f"VPN: {detector.vpn_connection.Id}")

# Check WiFi device
if detector.check_wifi_device():
    print(f"WiFi: {detector.wifi_device.Interface}")

# Check ethernet
has_ethernet = detector.check_ethernet_connection()

# Get VPN interface name
vpn_iface = detector.get_vpn_interface()  # Returns: 'nordlynx', 'tun0', etc.
```

### HotspotManager

Creates and manages WiFi hotspots.

```python
from src.network import HotspotManager

manager = HotspotManager()

# Create concurrent hotspot (virtual interface)
hotspot_info = manager.create_concurrent_hotspot(
    wifi_iface='wlo1',
    ssid='MyHotspot',
    password='securepass123',
    vpn_iface='nordlynx'
)

# Returns dict with:
# {
#     'hostapd': subprocess.Popen,
#     'dnsmasq': subprocess.Popen,
#     'ap_interface': 'wlo1_ap',
#     'wifi': 'wlo1',
#     'vpn': 'nordlynx'
# }

# Stop hotspot
manager.stop_hotspot(hotspot_info)
```

### RoutingManager

Manages IP forwarding and iptables rules.

```python
from src.network import RoutingManager

# Setup routing (static methods)
success = RoutingManager.setup_routing(
    wifi_iface='wlo1_ap',
    vpn_iface='nordlynx'
)

# Cleanup routing
RoutingManager.cleanup_routing(
    wifi_iface='wlo1_ap',
    vpn_iface='nordlynx'
)
```

## UI Module (`src/ui/`)

### TravelRouterApp

Main GTK4 application.

```python
from src.ui import TravelRouterApp

app = TravelRouterApp()
app.run(None)
```

**Key Methods:**

- `check_status()` - Check VPN and WiFi status
- `on_start_clicked()` - Start hotspot (triggered by button)
- `on_stop_clicked()` - Stop hotspot (triggered by button)
- `on_refresh_clicked()` - Refresh status display
- `show_error_dialog(message)` - Display error to user

## Utils Module (`src/utils/`)

### ConfigHandler

Encrypted configuration storage using system keyring.

```python
from src.utils import ConfigHandler

handler = ConfigHandler()

# Save encrypted config
config = {
    'api_key': 'secret123',
    'server': 'vpn.example.com'
}
handler.save_config(config)

# Load encrypted config
loaded_config = handler.load_config()
print(loaded_config['api_key'])  # 'secret123'
```

## Command-Line Usage

### Run Application

```bash
# Start GUI
python3 main.py
```

### Direct Network Testing

```python
#!/usr/bin/env python3
from src.network import NetworkDetector, HotspotManager, RoutingManager

# Check system status
detector = NetworkDetector()
detector.check_vpn_status()
detector.check_wifi_device()

# Create hotspot programmatically
if detector.vpn_connection and detector.wifi_device:
    manager = HotspotManager()
    hotspot = manager.create_concurrent_hotspot(
        wifi_iface=detector.wifi_device.Interface,
        ssid='TestHotspot',
        password='test12345',
        vpn_iface=detector.get_vpn_interface()
    )
    
    # Setup routing
    RoutingManager.setup_routing(
        hotspot['ap_interface'],
        hotspot['vpn']
    )
```

## Error Handling

All modules raise exceptions with descriptive messages:

```python
try:
    hotspot = manager.create_concurrent_hotspot(...)
except Exception as e:
    logger.error(f"Failed to create hotspot: {e}", exc_info=True)
    # Handle error (show dialog, retry, etc.)
```

## Logging

Logs are written to `travel_router_debug.log`:

```bash
# View logs in real-time
tail -f travel_router_debug.log

# Check for errors
grep ERROR travel_router_debug.log

# Filter by module
grep "NetworkDetector" travel_router_debug.log
```

## Testing

### Unit Testing Components

```python
import unittest
from src.network import NetworkDetector

class TestNetworkDetector(unittest.TestCase):
    def test_vpn_detection(self):
        detector = NetworkDetector()
        result = detector.check_vpn_status()
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```bash
# Run the diagnostic script
bash scripts/diagnose.sh

# Test concurrent AP mode
bash scripts/test_concurrent_ap.sh
```

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│           main.py (Entry Point)         │
│  - Initialize D-Bus                     │
│  - Launch GTK Application               │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼────────┐
         │   src/ui/      │
         │   app.py       │
         │  (GTK4 GUI)    │
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼────┐  ┌───▼────┐  ┌───▼────┐
│Network │  │Network │  │Routing │
│Detector│  │Hotspot │  │Manager │
└────────┘  └────────┘  └────────┘
    │            │            │
    └────────────┼────────────┘
                 │
         ┌───────▼────────┐
         │  NetworkManager│
         │  hostapd       │
         │  dnsmasq       │
         │  iptables      │
         └────────────────┘
```

## Module Dependencies

```
src/
├── core/          (No dependencies on other src modules)
├── network/       (Depends on: core)
│   ├── detector.py
│   ├── hotspot.py
│   └── routing.py
├── ui/            (Depends on: core, network)
│   └── app.py
└── utils/         (No dependencies on other src modules)
    └── config.py
```
