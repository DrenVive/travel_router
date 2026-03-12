# How Travel Shield Works - High Level Overview

## The Problem It Solves

You're at a hotel/airport with unsecured WiFi. You want to:
1. Connect to the WiFi
2. Protect yourself with VPN
3. Share that VPN-protected connection with your phone/tablet

**Travel Shield creates a WiFi hotspot that routes all traffic through your VPN.**

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Laptop                               │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Hotel    │───▶│   VPN    │───▶│ Internet │             │
│  │  WiFi    │    │ Tunnel   │    │          │             │
│  └──────────┘    └────┬─────┘    └──────────┘             │
│                       │                                      │
│                       │ (All traffic routed here)           │
│                       │                                      │
│                  ┌────▼─────┐                               │
│                  │ Hotspot  │                               │
│                  │ (wlo1_ap)│                               │
│                  └────┬─────┘                               │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        │ WiFi broadcast
                        │
              ┌─────────▼─────────┐
              │  Your Phone/      │
              │  Tablet/Devices   │
              └───────────────────┘
```

## The 5 Core Steps

### 1. **Detection** (`src/network/detector.py`)

When you launch the app, it scans your system:

```python
detector = NetworkDetector()

# Checks NetworkManager for active VPN
detector.check_vpn_status()
# Returns: True if WireGuard/OpenVPN/TUN found

# Finds your WiFi adapter
detector.check_wifi_device()
# Returns: True if WiFi card detected (e.g., wlo1)
```

**What it finds:**
- VPN interface: `nordlynx`, `tun0`, etc.
- WiFi interface: `wlo1`, `wlan0`, etc.

### 2. **Virtual Interface Creation** (`src/network/hotspot.py`)

Creates a second WiFi interface for the hotspot:

```bash
# Your laptop now has:
wlo1     # Connected to hotel WiFi
wlo1_ap  # Broadcasting hotspot (virtual interface)
```

**Key insight:** Modern WiFi cards can run **two modes simultaneously**:
- **Station mode** (wlo1) - Connected to internet
- **AP mode** (wlo1_ap) - Broadcasting hotspot

### 3. **Hotspot Configuration** (`src/network/hotspot.py`)

Three services get configured:

**a) hostapd** - Creates the WiFi access point
```
SSID: TravelShield
Password: your_password
Security: WPA2
Channel: 6 (2.4GHz) or same as your connection
```

**b) dnsmasq** - DHCP server for connected devices
```
IP Range: 192.168.50.10 - 192.168.50.100
Gateway: 192.168.50.1 (your laptop)
DNS: 8.8.8.8, 8.8.4.4
```

**c) IP Assignment**
```bash
wlo1_ap gets: 192.168.50.1/24
Phone gets: 192.168.50.x (via DHCP)
```

### 4. **Routing Setup** (`src/network/routing.py`)

This is the **magic** - forces all hotspot traffic through VPN:

```bash
# Enable IP forwarding (laptop acts as router)
sysctl -w net.ipv4.ip_forward=1

# iptables rules:
# 1. Allow traffic from hotspot to VPN
iptables -A FORWARD -i wlo1_ap -o nordlynx -j ACCEPT

# 2. Allow return traffic from VPN to hotspot
iptables -A FORWARD -i nordlynx -o wlo1_ap -m state --state RELATED,ESTABLISHED -j ACCEPT

# 3. NAT: Make hotspot traffic appear to come from VPN
iptables -t nat -A POSTROUTING -o nordlynx -j MASQUERADE
```

**Traffic flow:**
```
Phone (192.168.50.15) 
  → Laptop:wlo1_ap (192.168.50.1)
  → Laptop:nordlynx (VPN tunnel)
  → Internet
```

### 5. **GUI Display** (`src/ui/app.py`)

GTK4 interface shows status and controls:

```
┌─────────────────────────────────┐
│   Travel Shield VPN Router      │
├─────────────────────────────────┤
│ ✓ VPN Status: Connected         │
│ ✓ WiFi Device: wlo1              │
│ ○ Hotspot: Inactive              │
├─────────────────────────────────┤
│ Hotspot Name: [TravelShield   ] │
│ Password:     [●●●●●●●●●●●   ] │
├─────────────────────────────────┤
│ [Start VPN Hotspot] [Refresh]   │
└─────────────────────────────────┘
```

## Data Flow Example

Let's trace what happens when your phone requests `google.com`:

```
1. Phone → WiFi → Laptop (wlo1_ap:192.168.50.1)
   "Hey, I want to visit google.com"

2. Laptop checks iptables rules
   "This came from wlo1_ap, route it to nordlynx"

3. Laptop → VPN tunnel (nordlynx)
   "Request to google.com" (encrypted)

4. VPN Server → Internet → Google
   Google sees request from VPN server IP, not hotel WiFi

5. Google → VPN Server → Laptop (nordlynx)
   Response comes back through VPN

6. Laptop → Phone (wlo1_ap)
   "Here's the google.com page"
```

**Result:** Your phone's traffic is encrypted and appears to come from VPN location! 🔒

## Key Technologies

| Component | Purpose | What it does |
|-----------|---------|--------------|
| **NetworkManager** | System network management | Detects VPN/WiFi connections |
| **hostapd** | WiFi access point daemon | Broadcasts the hotspot SSID |
| **dnsmasq** | DHCP/DNS server | Gives IP addresses to connected devices |
| **iptables** | Linux firewall | Routes traffic through VPN |
| **iw** | WiFi configuration tool | Creates virtual interface |

## Why This Works

### Virtual Interface Magic

Modern WiFi cards support **concurrent operation**:
```
Physical card (phy0)
  ├── wlo1 (Station mode) - Receives internet
  └── wlo1_ap (AP mode) - Broadcasts hotspot
```

Both run at the same time on:
- **Same band**: e.g., both on 2.4GHz channel 6
- **Different bands**: wlo1 on 5GHz, wlo1_ap on 2.4GHz

### NAT (Network Address Translation)

```
Before NAT:
  Source: 192.168.50.15 (phone)
  Destination: 8.8.8.8 (Google DNS)

After NAT (MASQUERADE):
  Source: 10.x.x.x (VPN IP)
  Destination: 8.8.8.8 (Google DNS)
```

The internet sees your VPN IP, not your phone's local IP!

## Hardware Requirements Explained

**Why you need two network interfaces:**

❌ **Won't work:**
```
Hotel WiFi ← wlo1 → Hotspot
(Can't be client AND server on same interface without VPN already present)
```

✅ **Works:**
```
Option 1: Hotel WiFi ← wlo1    +  wlo1_ap → Hotspot
Option 2: Hotel WiFi ← eth0    +  wlo1 → Hotspot
Option 3: Phone USB  ← usb0    +  wlo1 → Hotspot
```

## Security Benefits

1. **Encryption**: All traffic encrypted through VPN tunnel
2. **Privacy**: Hotel can't see what sites you visit
3. **Protection**: Prevents man-in-the-middle attacks
4. **Location Masking**: Appear to be in VPN server location
5. **Device Coverage**: Protects devices without VPN support

## Summary

**In one sentence:**
Travel Shield creates a WiFi hotspot on your laptop that acts as a secure gateway, routing all connected devices' traffic through your VPN tunnel instead of directly to the hotel WiFi.

**What makes it special:**
- No need to install VPN on every device
- Hotel WiFi only sees encrypted VPN traffic
- Simple GUI - no terminal commands
- Concurrent operation - stay connected while sharing
- Automatic routing - just works!
