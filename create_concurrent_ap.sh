#!/bin/bash
# Script to create a WiFi hotspot while maintaining WiFi client connection
# Works with Intel Wi-Fi 6 AX201 and similar cards that support concurrent mode

set -e

SSID="${1:-TravelShield}"
PASSWORD="${2:-password123}"
INTERFACE="wlo1"

echo "Creating WiFi hotspot on $INTERFACE while keeping connection..."

# Get the channel of the current WiFi connection
CURRENT_CHANNEL=$(iw dev $INTERFACE info | grep channel | awk '{print $2}')
echo "Current WiFi channel: $CURRENT_CHANNEL"

# Create a virtual interface for AP mode
echo "Creating virtual interface..."
sudo iw dev $INTERFACE interface add ${INTERFACE}_ap type __ap

# Set the same channel for the AP
echo "Setting AP channel to match client: $CURRENT_CHANNEL"
sudo ip link set ${INTERFACE}_ap up

# Configure IP address for AP
echo "Configuring IP address..."
sudo ip addr add 192.168.50.1/24 dev ${INTERFACE}_ap

# Create hostapd configuration
cat > /tmp/hostapd.conf <<EOF
interface=${INTERFACE}_ap
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CURRENT_CHANNEL
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

echo "Configuration created at /tmp/hostapd.conf"
echo "To start the hotspot, run:"
echo "  sudo hostapd /tmp/hostapd.conf"
echo ""
echo "Then configure DHCP and routing separately"
