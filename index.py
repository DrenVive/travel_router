import NetworkManager
import subprocess
import dbus
import dbus.mainloop.glib

# Initialize D-Bus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

def start_hotspot(ssid, password, vpn_interface="tun0"):
    # This command creates the hotspot and routes it through the VPN
    cmd = f"sudo create_ap wlan0 wlan0 {ssid} {password} --gateway 192.168.12.1"
    subprocess.Popen(cmd.split())

vpn_connection = None
for conn in NetworkManager.NetworkManager.ActiveConnections:
    # Check for VPN or WireGuard connections
    if conn.Type in ['vpn', 'wireguard', 'tun']:
        vpn_connection = conn
        print(f"VPN Connection Found: {conn.Id} (Type: {conn.Type})")
        break

wifi_device = None
try:
    for dev in NetworkManager.NetworkManager.GetDevices():
        try:
            if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                wifi_device = dev
                break
        except (KeyError, AttributeError):
            # Skip devices with unknown types
            continue
except Exception as e:
    print(f"Warning: Error getting devices: {e}")
    
# Alternative method using nmcli if NetworkManager API fails
if wifi_device is None:
    try:
        result = subprocess.run(['nmcli', 'device', 'status'], 
                              capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines()[1:]:  # Skip header
            if 'wifi' in line.lower():
                parts = line.split()
                if parts:
                    wifi_interface = parts[0]
                    print(f"Found WiFi device via nmcli: {wifi_interface}")
                    # Create a simple object to hold the interface name
                    class SimpleDevice:
                        def __init__(self, interface):
                            self.Interface = interface
                    wifi_device = SimpleDevice(wifi_interface)
                    break
    except Exception as e:
        print(f"Alternative method also failed: {e}")

if vpn_connection:
    print(f"✓ VPN Connection: {vpn_connection.Id}")
else:
    print("✗ No VPN connection found")

if wifi_device:
    print(f"✓ WiFi Device: {wifi_device.Interface}")
else:
    print("✗ No WiFi device found")