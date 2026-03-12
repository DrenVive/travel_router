"""Network routing configuration"""

import subprocess
from ..core import logger


class RoutingManager:
    """Manages IP forwarding and routing rules"""
    
    @staticmethod
    def setup_routing(wifi_iface, vpn_iface):
        """Setup IP forwarding and routing rules"""
        try:
            logger.info(f"Setting up routing: {wifi_iface} -> {vpn_iface}")
            
            # Enable IP forwarding
            subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.ip_forward=1'], 
                         check=True, capture_output=True)
            logger.info("IP forwarding enabled")
            
            # Clear any existing rules for these interfaces
            RoutingManager._clear_existing_rules(wifi_iface, vpn_iface)
            
            # Add routing rules
            subprocess.run(['sudo', 'iptables', '-A', 'FORWARD', '-i', wifi_iface, 
                          '-o', vpn_iface, '-j', 'ACCEPT'], 
                         check=True, capture_output=True)
            logger.info(f"Added forward rule: {wifi_iface} -> {vpn_iface}")
            
            subprocess.run(['sudo', 'iptables', '-A', 'FORWARD', '-i', vpn_iface, 
                          '-o', wifi_iface, '-m', 'state', '--state', 'RELATED,ESTABLISHED', 
                          '-j', 'ACCEPT'], 
                         check=True, capture_output=True)
            logger.info(f"Added return forward rule: {vpn_iface} -> {wifi_iface}")
            
            subprocess.run(['sudo', 'iptables', '-t', 'nat', '-A', 'POSTROUTING', 
                          '-o', vpn_iface, '-j', 'MASQUERADE'], 
                         check=True, capture_output=True)
            logger.info(f"Added NAT masquerade rule for {vpn_iface}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup routing: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _clear_existing_rules(wifi_iface, vpn_iface):
        """Clear existing iptables rules for the interfaces"""
        subprocess.run(['sudo', 'iptables', '-D', 'FORWARD', '-i', wifi_iface, 
                      '-o', vpn_iface, '-j', 'ACCEPT'], 
                     check=False, capture_output=True)
        subprocess.run(['sudo', 'iptables', '-D', 'FORWARD', '-i', vpn_iface, 
                      '-o', wifi_iface, '-m', 'state', '--state', 'RELATED,ESTABLISHED', 
                      '-j', 'ACCEPT'], 
                     check=False, capture_output=True)
        subprocess.run(['sudo', 'iptables', '-t', 'nat', '-D', 'POSTROUTING', 
                      '-o', vpn_iface, '-j', 'MASQUERADE'], 
                     check=False, capture_output=True)
    
    @staticmethod
    def cleanup_routing(wifi_iface, vpn_iface):
        """Remove routing rules"""
        try:
            logger.info(f"Cleaning up routing rules: {wifi_iface} -> {vpn_iface}")
            RoutingManager._clear_existing_rules(wifi_iface, vpn_iface)
            logger.info("Routing rules cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up routing: {e}")
