#!/bin/bash
# Manual test script for concurrent WiFi hotspot

set -x  # Enable debug output

WIFI_IFACE="wlo1"
AP_IFACE="${WIFI_IFACE}_ap"
SSID="TravelShield"
PASSWORD="password123"

echo "=== Cleaning up any existing configuration ==="
sudo killall hostapd 2>/dev/null
sudo killall dnsmasq 2>/dev/null
sudo iw dev $AP_IFACE del 2>/dev/null

echo "=== Getting current WiFi channel ==="
CHANNEL=$(iw dev $WIFI_IFACE info | grep channel | awk '{print $2}')
echo "Current channel: $CHANNEL"

if [ -z "$CHANNEL" ]; then
    echo "Could not detect channel, using default 6"
    CHANNEL=6
fi

echo "=== Configuring NetworkManager to ignore AP interface ==="
sudo tee /etc/NetworkManager/conf.d/99-unmanaged-devices.conf <<EOF
[keyfile]
unmanaged-devices=interface-name:$AP_IFACE
EOF

echo "=== Reloading NetworkManager ==="
sudo systemctl reload NetworkManager
sleep 2

echo "=== Creating virtual interface ==="
sudo iw dev $WIFI_IFACE interface add $AP_IFACE type __ap
sleep 1

echo "=== Bringing up interface ==="
sudo ip link set $AP_IFACE up
sudo ip addr add 192.168.50.1/24 dev $AP_IFACE

echo "=== Verifying interface ==="
ip addr show $AP_IFACE

echo "=== Creating hostapd configuration ==="
cat > /tmp/hostapd_test.conf <<EOF
interface=$AP_IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

echo "=== Starting hostapd (press Ctrl+C to stop) ==="
sudo hostapd -dd /tmp/hostapd_test.conf
