"""Hotspot creation and management"""

import subprocess
import time
from ..core import logger


class HotspotManager:
    """Manages WiFi hotspot creation and configuration"""
    
    def __init__(self):
        self.hotspot_process = None
    
    def create_concurrent_hotspot(self, wifi_iface, ssid, password, vpn_iface):
        """Create hotspot using virtual interface (concurrent mode)"""
        try:
            ap_iface = f"{wifi_iface}_ap"
            
            # Get current channel and frequency
            result = subprocess.run(['iw', 'dev', wifi_iface, 'info'], 
                                  capture_output=True, text=True, check=True)
            channel, freq = self._parse_channel_info(result.stdout)
            
            if not channel or not freq:
                raise Exception(f"Could not detect WiFi channel/frequency. Output:\n{result.stdout}")
            
            # Determine hardware mode and channel
            hw_mode, use_channel = self._determine_hw_mode(channel, freq)
            logger.info(f"Using channel {use_channel} with hw_mode={hw_mode} for concurrent AP")
            
            # Setup virtual interface
            self._setup_virtual_interface(wifi_iface, ap_iface)
            
            # Start hostapd
            hostapd_proc = self._start_hostapd(ap_iface, ssid, password, hw_mode, use_channel)
            
            # Start dnsmasq for DHCP
            dnsmasq_proc = self._start_dnsmasq(ap_iface)
            
            return {
                'hostapd': hostapd_proc,
                'dnsmasq': dnsmasq_proc,
                'ap_interface': ap_iface,
                'wifi': wifi_iface,
                'vpn': vpn_iface
            }
            
        except Exception as e:
            logger.error(f"Failed to create concurrent hotspot: {e}", exc_info=True)
            self._cleanup_on_failure(locals().get('ap_iface'))
            raise
    
    def _parse_channel_info(self, iw_output):
        """Parse channel and frequency from iw output"""
        channel = None
        freq = None
        
        for line in iw_output.splitlines():
            line = line.strip()
            if line.startswith('channel'):
                parts = line.split()
                if len(parts) >= 3:
                    channel = parts[1]
                    freq_part = parts[2].replace('(', '').replace(')', '')
                    try:
                        freq = int(freq_part)
                        logger.debug(f"Parsed channel={channel}, freq={freq}")
                        break
                    except ValueError:
                        logger.debug(f"Failed to parse frequency from: {parts[2]}")
                        continue
        
        return channel, freq
    
    def _determine_hw_mode(self, channel, freq):
        """Determine hardware mode and channel based on frequency"""
        # DFS channels (52-144) cause issues in concurrent mode
        dfs_channels = list(range(52, 145, 4))
        
        if freq < 3000:
            # 2.4 GHz
            return 'g', channel
        elif int(channel) in dfs_channels:
            # DFS channel detected, fall back to 2.4GHz channel 6
            logger.warning(f"Channel {channel} is a DFS channel, falling back to 2.4GHz channel 6")
            return 'g', '6'
        else:
            # Non-DFS 5GHz channel (149-165)
            return 'a', channel
    
    def _setup_virtual_interface(self, wifi_iface, ap_iface):
        """Setup virtual AP interface"""
        # Clean up any existing virtual interface
        subprocess.run(['sudo', 'iw', 'dev', ap_iface, 'del'], 
                     check=False, capture_output=True)
        
        # Configure NetworkManager to ignore AP interface
        logger.info("Configuring NetworkManager to ignore AP interface")
        nm_conf = f"""[keyfile]
unmanaged-devices=interface-name:{ap_iface}
"""
        conf_path = '/etc/NetworkManager/conf.d/99-unmanaged-devices.conf'
        subprocess.run(['sudo', 'tee', conf_path], 
                     input=nm_conf.encode(), 
                     check=True, capture_output=True)
        
        # Reload NetworkManager config
        subprocess.run(['sudo', 'systemctl', 'reload', 'NetworkManager'], 
                     check=True, capture_output=True)
        time.sleep(2)
        
        # Create virtual interface
        logger.info(f"Creating virtual interface {ap_iface}")
        subprocess.run(['sudo', 'iw', 'dev', wifi_iface, 'interface', 'add', 
                      ap_iface, 'type', '__ap'], check=True, capture_output=True)
        time.sleep(1)
        
        # Bring up interface
        subprocess.run(['sudo', 'ip', 'link', 'set', ap_iface, 'up'], 
                     check=True, capture_output=True)
        
        # Configure IP
        subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', ap_iface], 
                     check=False, capture_output=True)
        subprocess.run(['sudo', 'ip', 'addr', 'add', '192.168.50.1/24', 
                      'dev', ap_iface], check=True, capture_output=True)
        
        logger.info(f"Interface {ap_iface} configured with IP 192.168.50.1")
    
    def _start_hostapd(self, ap_iface, ssid, password, hw_mode, channel):
        """Start hostapd daemon"""
        hostapd_conf = f"""interface={ap_iface}
driver=nl80211
ssid={ssid}
hw_mode={hw_mode}
channel={channel}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        # Add performance options
        if hw_mode == 'a':
            hostapd_conf += "country_code=GB\nieee80211d=1\nieee80211n=1\nieee80211ac=1\n"
        elif hw_mode == 'g':
            hostapd_conf += "ieee80211n=1\n"
        
        conf_path = '/tmp/travel_router_hostapd.conf'
        with open(conf_path, 'w') as f:
            f.write(hostapd_conf)
        
        logger.info(f"hostapd config written to {conf_path}")
        
        # Start hostapd in background
        logger.info("Starting hostapd...")
        log_file = open('/tmp/hostapd.log', 'w')
        hostapd_proc = subprocess.Popen(['sudo', 'hostapd', '-dd', conf_path],
                                       stdout=log_file,
                                       stderr=subprocess.STDOUT)
        
        # Wait for hostapd to start
        time.sleep(3)
        
        # Check if hostapd is still running
        if hostapd_proc.poll() is not None:
            with open('/tmp/hostapd.log', 'r') as f:
                stderr = f.read()
            logger.error(f"hostapd output: {stderr}")
            raise Exception(f"hostapd failed to start. Check /tmp/hostapd.log for details")
        
        logger.info("hostapd started successfully")
        return hostapd_proc
    
    def _start_dnsmasq(self, ap_iface):
        """Start dnsmasq for DHCP"""
        logger.info("Configuring DHCP...")
        subprocess.run(['sudo', 'killall', 'dnsmasq'], 
                     check=False, capture_output=True)
        
        dnsmasq_conf = f"""interface={ap_iface}
dhcp-range=192.168.50.10,192.168.50.100,12h
dhcp-option=3,192.168.50.1
dhcp-option=6,8.8.8.8,8.8.4.4
bind-interfaces
"""
        dnsmasq_conf_path = '/tmp/travel_router_dnsmasq.conf'
        with open(dnsmasq_conf_path, 'w') as f:
            f.write(dnsmasq_conf)
        
        dnsmasq_log = open('/tmp/dnsmasq.log', 'w')
        dnsmasq_proc = subprocess.Popen(['sudo', 'dnsmasq', '-C', dnsmasq_conf_path, '-d'],
                                       stdout=dnsmasq_log,
                                       stderr=subprocess.STDOUT)
        
        logger.info("dnsmasq started")
        return dnsmasq_proc
    
    def _cleanup_on_failure(self, ap_iface):
        """Cleanup on hotspot creation failure"""
        subprocess.run(['sudo', 'killall', 'hostapd'], check=False, capture_output=True)
        subprocess.run(['sudo', 'killall', 'dnsmasq'], check=False, capture_output=True)
        if ap_iface:
            subprocess.run(['sudo', 'iw', 'dev', ap_iface, 'del'], 
                         check=False, capture_output=True)
    
    def stop_hotspot(self, hotspot_info):
        """Stop running hotspot"""
        try:
            if isinstance(hotspot_info, dict):
                ap_iface = hotspot_info.get('ap_interface')
                
                # Stop processes
                if 'hostapd' in hotspot_info:
                    logger.info("Stopping hostapd...")
                    hotspot_info['hostapd'].terminate()
                    hotspot_info['hostapd'].wait(timeout=5)
                
                if 'dnsmasq' in hotspot_info:
                    logger.info("Stopping dnsmasq...")
                    hotspot_info['dnsmasq'].terminate()
                    hotspot_info['dnsmasq'].wait(timeout=5)
                
                # Remove virtual interface
                if ap_iface:
                    logger.info(f"Removing virtual interface {ap_iface}")
                    subprocess.run(['sudo', 'iw', 'dev', ap_iface, 'del'], 
                                 check=False, capture_output=True)
            
            # Fallback cleanup
            subprocess.run(['sudo', 'killall', 'hostapd'], check=False, capture_output=True)
            subprocess.run(['sudo', 'killall', 'dnsmasq'], check=False, capture_output=True)
            
            logger.info("Hotspot stopped")
        except Exception as e:
            logger.error(f"Error stopping hotspot: {e}", exc_info=True)
            raise
