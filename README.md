# Travel Shield - VPN Travel Router

A GTK4 application that turns your Linux laptop into a VPN-enabled WiFi hotspot for secure travel internet sharing.

## Features

- 🔒 **VPN Routing** - All hotspot traffic routes through your VPN
- 📡 **WiFi Hotspot** - Share internet with multiple devices
- 🖥️ **GTK4 GUI** - Modern, user-friendly interface
- 🔍 **Auto-detection** - Finds VPN and WiFi interfaces automatically
- 📝 **Debug Logging** - Complete activity logs for troubleshooting
- 🔐 **Encrypted Config** - Secure configuration storage with system keyring

## Requirements

⚠️ **IMPORTANT:** You need **TWO** network interfaces:
1. **One for internet input** (Ethernet OR WiFi adapter)
2. **One for hotspot output** (WiFi adapter)

### Hardware Options

**Option A (Recommended):**
- Laptop with built-in WiFi
- Ethernet cable connection

**Option B:**
- Laptop with built-in WiFi
- USB WiFi adapter

**Won't Work:**
- ❌ Single WiFi interface only
- ❌ Trying to connect to WiFi AND broadcast hotspot on same adapter

## Installation

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 \
                 pkg-config libdbus-1-dev libglib2.0-dev

# Create virtual environment
cd travel_router
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install Python packages
pip install cryptography keyring python-networkmanager
```

## Usage

```bash
# Run the GUI application
python3 gui.py

# Or from system Python (if packages installed globally)
python3 /path/to/travel_router/gui.py
```

### Steps:
1. Connect to internet via Ethernet (or ensure you have 2 WiFi adapters)
2. Connect to your VPN (NordVPN, WireGuard, OpenVPN, etc.)
3. Launch Travel Shield
4. Verify VPN and WiFi status are ✓ green
5. Enter hotspot name and password
6. Click "Start VPN Hotspot"
7. Connect your phone/devices to the hotspot
8. All traffic routes through VPN! 🎉

## Project Structure

```
travel_router/
├── gui.py                    # Main GTK4 application
├── index.py                  # CLI version (basic)
├── encrypt.py                # Configuration encryption handler
├── SETUP_GUIDE.md           # Detailed setup instructions
├── travel_router_debug.log  # Debug log (auto-generated)
└── config.json              # Encrypted config (auto-generated)
```

## How It Works

1. **Detection**: Scans for active VPN connections (vpn, wireguard, tun)
2. **Hotspot Creation**: Uses NetworkManager to create WiFi AP
3. **IP Forwarding**: Enables kernel IP forwarding
4. **iptables Rules**: 
   - Forward traffic from WiFi → VPN interface
   - NAT/Masquerade on VPN interface
   - Return traffic from VPN → WiFi
5. **Routing**: All connected devices' traffic goes through VPN

## Troubleshooting

### "No internet on connected devices"
- Ensure you have 2 network interfaces (see Requirements)
- Check debug log: `tail -f travel_router_debug.log`
- Verify VPN is connected before starting hotspot

### "Laptop loses internet when hotspot starts"
- Normal if using WiFi for both internet AND hotspot
- Solution: Use Ethernet or add USB WiFi adapter
- See SETUP_GUIDE.md for details

### "VPN not detected"
- Currently supports: OpenVPN, WireGuard, TUN interfaces
- Check: `nmcli connection show --active`
- VPN must be active BEFORE starting hotspot

## Debug Logging

All activity is logged to `travel_router_debug.log`:
```bash
# Watch logs in real-time
tail -f travel_router_debug.log

# View recent errors
grep ERROR travel_router_debug.log
```

## Security Notes

- Configuration encrypted using Fernet (symmetric encryption)
- Encryption key stored in system keyring (GNOME Keyring/KWallet)
- Hotspot password minimum 8 characters
- All traffic routed through VPN (no leaks)

## Supported VPN Types

- ✅ OpenVPN
- ✅ WireGuard (NordLynx, etc.)
- ✅ TUN-based VPNs
- ⚠️ May need adjustment for other types

## Known Limitations

- Single WiFi interface cannot be client + AP simultaneously
- Requires sudo for iptables and NetworkManager operations
- GTK4 required (won't run on older systems)

## License

MIT License - Feel free to use and modify

## Contributing

Issues and PRs welcome! Please test thoroughly before submitting.

## Credits

Built with:
- Python 3.12+
- GTK 4
- NetworkManager
- python-networkmanager
- cryptography
- keyring
