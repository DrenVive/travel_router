"""Network detection and management"""

import NetworkManager
import subprocess
from ..core import logger


class NetworkDetector:
    """Detects VPN connections and WiFi devices"""
    
    def __init__(self):
        self.vpn_connection = None
        self.wifi_device = None
    
    def check_vpn_status(self):
        """Check for active VPN connection"""
        self.vpn_connection = None
        try:
            for conn in NetworkManager.NetworkManager.ActiveConnections:
                if conn.Type in ['vpn', 'wireguard', 'tun']:
                    self.vpn_connection = conn
                    logger.info(f"VPN connection found: {conn.Id} (Type: {conn.Type})")
                    return True
            
            logger.warning("No VPN connection found")
            return False
        except Exception as e:
            logger.error(f"Error checking VPN status: {e}")
            return False
    
    def check_wifi_device(self):
        """Check for WiFi device"""
        self.wifi_device = None
        
        # Try NetworkManager first
        try:
            logger.debug("Checking WiFi devices via NetworkManager...")
            for dev in NetworkManager.NetworkManager.GetDevices():
                try:
                    if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                        self.wifi_device = dev
                        logger.info(f"WiFi device found: {dev.Interface}")
                        return True
                except (KeyError, AttributeError) as e:
                    logger.debug(f"Skipping device due to error: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Error enumerating devices via NetworkManager: {e}")
        
        # Fallback to nmcli
        if self.wifi_device is None:
            logger.debug("Trying fallback method with nmcli...")
            try:
                result = subprocess.run(['nmcli', 'device', 'status'], 
                                      capture_output=True, text=True, check=True)
                for line in result.stdout.splitlines()[1:]:
                    if 'wifi' in line.lower() and 'p2p' not in line.lower():
                        parts = line.split()
                        if parts:
                            class SimpleDevice:
                                def __init__(self, interface):
                                    self.Interface = interface
                            self.wifi_device = SimpleDevice(parts[0])
                            logger.info(f"WiFi device found via nmcli: {parts[0]}")
                            return True
            except Exception as e:
                logger.error(f"Fallback method failed: {e}")
        
        if not self.wifi_device:
            logger.warning("No WiFi device found")
        
        return self.wifi_device is not None
    
    def check_ethernet_connection(self):
        """Check if there's an ethernet connection"""
        try:
            for conn in NetworkManager.NetworkManager.ActiveConnections:
                if conn.Type == 'ethernet' or conn.Type == '802-3-ethernet':
                    for dev in conn.Devices:
                        if hasattr(dev, 'Interface'):
                            logger.info(f"Ethernet connection found: {dev.Interface}")
                            return True
        except Exception as e:
            logger.debug(f"Error checking ethernet: {e}")
        return False
    
    def get_vpn_interface(self):
        """Get the VPN interface name"""
        try:
            # Try to get from connection
            if hasattr(self.vpn_connection, 'Devices') and self.vpn_connection.Devices:
                for dev in self.vpn_connection.Devices:
                    if hasattr(dev, 'Interface'):
                        return dev.Interface
            
            # Fallback: check for common VPN interfaces
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if 'tun' in line or 'nordlynx' in line or 'wg' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        iface = parts[1].strip().split('@')[0]
                        logger.info(f"Found VPN interface: {iface}")
                        return iface
            
            # Last resort: use nordlynx since we detected it
            return 'nordlynx'
        except Exception as e:
            logger.error(f"Error getting VPN interface: {e}")
            return None
