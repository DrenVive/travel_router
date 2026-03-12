#!/bin/bash
# Diagnostic script to check network routing

echo "=== Network Interfaces ==="
ip link show

echo -e "\n=== IP Addresses ==="
ip addr show

echo -e "\n=== Routing Table ==="
ip route show

echo -e "\n=== IP Forwarding Status ==="
sysctl net.ipv4.ip_forward

echo -e "\n=== Active Connections (nmcli) ==="
nmcli connection show --active

echo -e "\n=== Hotspot Status ==="
nmcli connection show Hotspot 2>/dev/null || echo "Hotspot not found"

echo -e "\n=== iptables NAT Rules ==="
sudo iptables -t nat -L -n -v

echo -e "\n=== iptables FORWARD Rules ==="
sudo iptables -L FORWARD -n -v

echo -e "\n=== DNS Configuration ==="
cat /etc/resolv.conf
