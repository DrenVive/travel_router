import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import NetworkManager
import subprocess
import dbus
import dbus.mainloop.glib
import threading
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('travel_router_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('TravelRouter')

# Initialize D-Bus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
logger.info("D-Bus main loop initialized")

class TravelRouterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.travelrouter.app')
        self.vpn_connection = None
        self.wifi_device = None
        self.hotspot_process = None
        logger.info("TravelRouterApp initialized")
        
        # Connect to shutdown signal to cleanup properly
        self.connect('shutdown', self.on_shutdown)
        
    def do_activate(self):
        logger.info("Application activating...")
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("Travel Shield")
        win.set_default_size(400, 300)
        
        # Connect close request handler
        win.connect('close-request', self.on_window_close_request)
        
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Travel Shield VPN Router</span>")
        box.append(title)
        
        # Status section
        status_frame = Gtk.Frame()
        status_frame.set_margin_top(10)
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        status_box.set_margin_top(10)
        status_box.set_margin_bottom(10)
        status_box.set_margin_start(10)
        status_box.set_margin_end(10)
        
        self.vpn_status_label = Gtk.Label(label="VPN Status: Checking...")
        self.vpn_status_label.set_halign(Gtk.Align.START)
        status_box.append(self.vpn_status_label)
        
        self.wifi_status_label = Gtk.Label(label="WiFi Device: Checking...")
        self.wifi_status_label.set_halign(Gtk.Align.START)
        status_box.append(self.wifi_status_label)
        
        self.hotspot_status_label = Gtk.Label(label="Hotspot: Inactive")
        self.hotspot_status_label.set_halign(Gtk.Align.START)
        status_box.append(self.hotspot_status_label)
        
        status_frame.set_child(status_box)
        box.append(status_frame)
        
        # Configuration section
        config_frame = Gtk.Frame()
        config_frame.set_margin_top(10)
        config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        config_box.set_margin_top(10)
        config_box.set_margin_bottom(10)
        config_box.set_margin_start(10)
        config_box.set_margin_end(10)
        
        # SSID input
        ssid_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ssid_label = Gtk.Label(label="Hotspot Name:")
        ssid_label.set_width_chars(15)
        ssid_label.set_halign(Gtk.Align.START)
        self.ssid_entry = Gtk.Entry()
        self.ssid_entry.set_text("TravelShield")
        self.ssid_entry.set_hexpand(True)
        ssid_box.append(ssid_label)
        ssid_box.append(self.ssid_entry)
        config_box.append(ssid_box)
        
        # Password input
        pass_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pass_label = Gtk.Label(label="Password:")
        pass_label.set_width_chars(15)
        pass_label.set_halign(Gtk.Align.START)
        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_text("password123")
        self.pass_entry.set_visibility(False)
        self.pass_entry.set_hexpand(True)
        pass_box.append(pass_label)
        pass_box.append(self.pass_entry)
        config_box.append(pass_box)
        
        config_frame.set_child(config_box)
        box.append(config_frame)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(20)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.start_button = Gtk.Button(label="Start VPN Hotspot")
        self.start_button.connect('clicked', self.on_start_clicked)
        self.start_button.add_css_class('suggested-action')
        button_box.append(self.start_button)
        
        self.stop_button = Gtk.Button(label="Stop Hotspot")
        self.stop_button.connect('clicked', self.on_stop_clicked)
        self.stop_button.set_sensitive(False)
        self.stop_button.add_css_class('destructive-action')
        button_box.append(self.stop_button)
        
        self.refresh_button = Gtk.Button(label="Refresh Status")
        self.refresh_button.connect('clicked', self.on_refresh_clicked)
        button_box.append(self.refresh_button)
        
        box.append(button_box)
        
        win.set_child(box)
        win.present()
        
        logger.info("Window presented, checking initial status...")
        # Check initial status
        GLib.timeout_add(100, self.check_status)
    
    def on_window_close_request(self, window):
        """Handle window close request"""
        logger.info("Window close requested")
        
        # Stop hotspot if running
        if self.hotspot_process:
            logger.info("Stopping hotspot before closing...")
            try:
                self.on_stop_clicked(None)
            except Exception as e:
                logger.error(f"Error stopping hotspot: {e}")
        
        logger.info("Closing application")
        return False  # Allow the window to close
    
    def on_shutdown(self, app):
        """Cleanup on application shutdown"""
        logger.info("Application shutting down...")
        
        # Cleanup routing and hotspot
        if self.hotspot_process:
            try:
                if isinstance(self.hotspot_process, dict):
                    wifi_iface = self.hotspot_process.get('wifi')
                    vpn_iface = self.hotspot_process.get('vpn')
                    if wifi_iface and vpn_iface:
                        self.cleanup_routing(wifi_iface, vpn_iface)
                
                # Stop hotspot connection
                subprocess.run(['sudo', 'nmcli', 'connection', 'down', 'Hotspot'], 
                             check=False, capture_output=True)
                logger.info("Hotspot stopped during shutdown")
            except Exception as e:
                logger.error(f"Error stopping hotspot during shutdown: {e}")
        
        logger.info("Shutdown complete")
    
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
    
    def check_status(self):
        """Check VPN and WiFi status"""
        logger.debug("Checking VPN and WiFi status...")
        
        # Check VPN
        self.vpn_connection = None
        try:
            for conn in NetworkManager.NetworkManager.ActiveConnections:
                if conn.Type in ['vpn', 'wireguard', 'tun']:
                    self.vpn_connection = conn
                    logger.info(f"VPN connection found: {conn.Id} (Type: {conn.Type})")
                    self.vpn_status_label.set_markup(
                        f"<span foreground='green'>✓ VPN Status: Connected ({conn.Id})</span>"
                    )
                    break
            
            if not self.vpn_connection:
                logger.warning("No VPN connection found")
                self.vpn_status_label.set_markup(
                    "<span foreground='red'>✗ VPN Status: Not Connected</span>"
                )
        except Exception as e:
            logger.error(f"Error checking VPN status: {e}")
            self.vpn_status_label.set_text(f"VPN Status: Error - {e}")
        
        # Check WiFi device
        self.wifi_device = None
        try:
            logger.debug("Checking WiFi devices via NetworkManager...")
            for dev in NetworkManager.NetworkManager.GetDevices():
                try:
                    if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                        self.wifi_device = dev
                        logger.info(f"WiFi device found: {dev.Interface}")
                        break
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
                            break
            except Exception as e:
                logger.error(f"Fallback method failed: {e}")
        
        if self.wifi_device:
            self.wifi_status_label.set_markup(
                f"<span foreground='green'>✓ WiFi Device: {self.wifi_device.Interface}</span>"
            )
        else:
            logger.warning("No WiFi device found")
            self.wifi_status_label.set_markup(
                "<span foreground='red'>✗ WiFi Device: Not Found</span>"
            )
        
        logger.debug("Status check complete")
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
                # Look for tun, nordlynx, or other VPN interfaces
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
    
    def setup_routing(self, wifi_iface, vpn_iface):
        """Setup IP forwarding and routing rules"""
        try:
            logger.info(f"Setting up routing: {wifi_iface} -> {vpn_iface}")
            
            # Enable IP forwarding
            subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.ip_forward=1'], 
                         check=True, capture_output=True)
            logger.info("IP forwarding enabled")
            
            # Clear any existing rules for these interfaces
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
    
    def cleanup_routing(self, wifi_iface, vpn_iface):
        """Remove routing rules"""
        try:
            logger.info(f"Cleaning up routing rules: {wifi_iface} -> {vpn_iface}")
            
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
            
            logger.info("Routing rules cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up routing: {e}")
    
    def create_concurrent_hotspot(self, wifi_iface, ssid, password, vpn_iface):
        """Create hotspot using virtual interface (concurrent mode)"""
        try:
            ap_iface = f"{wifi_iface}_ap"
            
            # Get current channel and frequency
            result = subprocess.run(['iw', 'dev', wifi_iface, 'info'], 
                                  capture_output=True, text=True, check=True)
            channel = None
            freq = None
            
            # Parse output line by line
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith('channel'):
                    # Example: "channel 136 (5680 MHz), width: 40 MHz, center1: 5670 MHz"
                    parts = line.split()
                    # parts[0] = 'channel', parts[1] = '136', parts[2] = '(5680', parts[3] = 'MHz),'
                    if len(parts) >= 3:
                        channel = parts[1]
                        # Extract frequency from something like '(5680'
                        freq_part = parts[2].replace('(', '').replace(')', '')
                        try:
                            freq = int(freq_part)
                            logger.debug(f"Parsed channel={channel}, freq={freq}")
                            break
                        except ValueError:
                            logger.debug(f"Failed to parse frequency from: {parts[2]}")
                            continue
            
            if not channel or not freq:
                raise Exception(f"Could not detect WiFi channel/frequency. Output:\n{result.stdout}")
            
            # Determine hardware mode based on frequency
            # DFS channels (52-144) cause issues in concurrent mode, use 2.4GHz instead
            dfs_channels = list(range(52, 145, 4))  # DFS channels: 52, 56, 60...144
            
            if freq < 3000:
                hw_mode = 'g'  # 2.4 GHz
                use_channel = channel
            elif int(channel) in dfs_channels:
                # DFS channel detected, fall back to 2.4GHz channel 6
                logger.warning(f"Channel {channel} is a DFS channel, falling back to 2.4GHz channel 6")
                hw_mode = 'g'
                use_channel = '6'
            else:
                # Non-DFS 5GHz channel (149-165)
                hw_mode = 'a'
                use_channel = channel
            
            logger.info(f"Using channel {use_channel} with hw_mode={hw_mode} for concurrent AP (original: {channel}@{freq}MHz)")
            
            # Clean up any existing virtual interface
            subprocess.run(['sudo', 'iw', 'dev', ap_iface, 'del'], 
                         check=False, capture_output=True)
            
            # Stop NetworkManager from managing the AP interface
            logger.info("Configuring NetworkManager to ignore AP interface")
            nm_conf = """[keyfile]
unmanaged-devices=interface-name:wlo1_ap
"""
            conf_path = '/etc/NetworkManager/conf.d/99-unmanaged-devices.conf'
            subprocess.run(['sudo', 'tee', conf_path], 
                         input=nm_conf.encode(), 
                         check=True, capture_output=True)
            
            # Reload NetworkManager config
            subprocess.run(['sudo', 'systemctl', 'reload', 'NetworkManager'], 
                         check=True, capture_output=True)
            
            import time
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
            
            # Create hostapd config
            hostapd_conf = f"""interface={ap_iface}
driver=nl80211
ssid={ssid}
hw_mode={hw_mode}
channel={use_channel}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
            # Add country code and 802.11n/ac for better performance
            if hw_mode == 'a':
                hostapd_conf += "country_code=GB\n"
                hostapd_conf += "ieee80211d=1\n"
                hostapd_conf += "ieee80211n=1\n"
                hostapd_conf += "ieee80211ac=1\n"
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
            
            # Wait a bit for hostapd to start
            time.sleep(3)
            
            # Check if hostapd is still running
            if hostapd_proc.poll() is not None:
                with open('/tmp/hostapd.log', 'r') as f:
                    stderr = f.read()
                logger.error(f"hostapd output: {stderr}")
                raise Exception(f"hostapd failed to start. Check /tmp/hostapd.log for details")
            
            logger.info("hostapd started successfully")
            
            # Configure dnsmasq for DHCP
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
            
            # Setup routing
            logger.info("Setting up routing...")
            if not self.setup_routing(ap_iface, vpn_iface):
                raise Exception("Failed to setup routing")
            
            return {
                'hostapd': hostapd_proc,
                'dnsmasq': dnsmasq_proc,
                'ap_interface': ap_iface,
                'wifi': wifi_iface,
                'vpn': vpn_iface
            }
            
        except Exception as e:
            logger.error(f"Failed to create concurrent hotspot: {e}", exc_info=True)
            # Cleanup on failure
            subprocess.run(['sudo', 'killall', 'hostapd'], check=False, capture_output=True)
            subprocess.run(['sudo', 'killall', 'dnsmasq'], check=False, capture_output=True)
            if 'ap_iface' in locals():
                subprocess.run(['sudo', 'iw', 'dev', ap_iface, 'del'], check=False, capture_output=True)
            raise
    
    def on_start_clicked(self, button):
        """Start the VPN hotspot"""
        logger.info("Start button clicked")
        
        if not self.vpn_connection:
            logger.warning("Cannot start hotspot - no VPN connection")
            self.show_error_dialog("No VPN connection detected. Please connect to a VPN first.")
            return
        
        if not self.wifi_device:
            logger.warning("Cannot start hotspot - no WiFi device")
            self.show_error_dialog("No WiFi device found. Cannot create hotspot.")
            return
        
        # Check if ethernet is connected
        has_ethernet = self.check_ethernet_connection()
        wifi_iface = self.wifi_device.Interface
        
        # Check if WiFi card supports concurrent mode
        logger.info(f"Attempting concurrent AP+STA mode on {wifi_iface}")
        
        if not has_ethernet:
            logger.info("No ethernet found, will use concurrent WiFi mode")
        
        ssid = self.ssid_entry.get_text()
        password = self.pass_entry.get_text()
        
        logger.info(f"Starting hotspot with SSID: {ssid}")
        
        if len(password) < 8:
            logger.warning("Password too short")
            self.show_error_dialog("Password must be at least 8 characters long.")
            return
        
        # Start hotspot in background thread
        def start_hotspot():
            try:
                vpn_iface = self.get_vpn_interface()
                
                if not vpn_iface:
                    GLib.idle_add(self.show_error_dialog, 
                                "Could not determine VPN interface.")
                    GLib.idle_add(lambda: self.start_button.set_sensitive(True))
                    return
                
                logger.info(f"Creating concurrent hotspot: {wifi_iface} + {wifi_iface}_ap -> {vpn_iface}")
                
                # Use concurrent mode (virtual interface)
                self.hotspot_process = self.create_concurrent_hotspot(
                    wifi_iface, ssid, password, vpn_iface
                )
                
                logger.info("Concurrent hotspot configured successfully")
                GLib.idle_add(self.on_hotspot_started)
                
            except Exception as e:
                logger.error(f"Failed to start hotspot: {e}", exc_info=True)
                GLib.idle_add(self.show_error_dialog, f"Failed to start hotspot: {e}")
                GLib.idle_add(lambda: self.start_button.set_sensitive(True))
                
            except Exception as e:
                logger.error(f"Failed to start hotspot: {e}", exc_info=True)
                GLib.idle_add(self.show_error_dialog, f"Failed to start hotspot: {e}")
        
        thread = threading.Thread(target=start_hotspot)
        thread.daemon = True
        thread.start()
        
        self.start_button.set_sensitive(False)
        self.hotspot_status_label.set_markup(
            "<span foreground='orange'>Hotspot: Starting...</span>"
        )
    
    def on_hotspot_started(self):
        """Called when hotspot is started successfully"""
        logger.info("Hotspot started successfully")
        self.hotspot_status_label.set_markup(
            "<span foreground='green'>✓ Hotspot: Active</span>"
        )
        self.stop_button.set_sensitive(True)
        self.start_button.set_sensitive(False)
    
    def on_stop_clicked(self, button):
        """Stop the VPN hotspot"""
        logger.info("Stop button clicked")
        try:
            # Cleanup routing first
            if self.hotspot_process and isinstance(self.hotspot_process, dict):
                ap_iface = self.hotspot_process.get('ap_interface')
                vpn_iface = self.hotspot_process.get('vpn')
                
                if ap_iface and vpn_iface:
                    self.cleanup_routing(ap_iface, vpn_iface)
                
                # Stop processes
                if 'hostapd' in self.hotspot_process:
                    logger.info("Stopping hostapd...")
                    self.hotspot_process['hostapd'].terminate()
                    self.hotspot_process['hostapd'].wait(timeout=5)
                
                if 'dnsmasq' in self.hotspot_process:
                    logger.info("Stopping dnsmasq...")
                    self.hotspot_process['dnsmasq'].terminate()
                    self.hotspot_process['dnsmasq'].wait(timeout=5)
                
                # Remove virtual interface
                if ap_iface:
                    logger.info(f"Removing virtual interface {ap_iface}")
                    subprocess.run(['sudo', 'iw', 'dev', ap_iface, 'del'], 
                                 check=False, capture_output=True)
            
            # Fallback cleanup
            subprocess.run(['sudo', 'killall', 'hostapd'], check=False, capture_output=True)
            subprocess.run(['sudo', 'killall', 'dnsmasq'], check=False, capture_output=True)
            
            logger.info("Hotspot stopped")
            self.hotspot_status_label.set_markup(
                "<span foreground='gray'>Hotspot: Inactive</span>"
            )
            self.stop_button.set_sensitive(False)
            self.start_button.set_sensitive(True)
            self.hotspot_process = None
        except Exception as e:
            logger.error(f"Failed to stop hotspot: {e}", exc_info=True)
            self.show_error_dialog(f"Failed to stop hotspot: {e}")
    
    def on_refresh_clicked(self, button):
        """Refresh the status"""
        logger.info("Refresh button clicked")
        self.check_status()
    
    def show_error_dialog(self, message):
        """Show an error dialog"""
        logger.error(f"Showing error dialog: {message}")
        dialog = Gtk.AlertDialog()
        dialog.set_message("Error")
        dialog.set_detail(message)
        dialog.show(self.get_active_window())
    
    def show_warning_dialog(self, title, message):
        """Show a warning dialog with Yes/No buttons"""
        logger.warning(f"Showing warning dialog: {title}")
        dialog = Gtk.AlertDialog()
        dialog.set_message(title)
        dialog.set_detail(message)
        dialog.set_buttons(["Cancel", "Continue"])
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)
        
        # Use choose to get the button response
        def on_response(dialog, result):
            try:
                response = dialog.choose_finish(result)
                return response == 1  # 1 = Continue button
            except:
                return False
        
        # For simplicity in this context, we'll use a simpler approach
        # Return False for now (user should get ethernet first)
        return False

def main():
    logger.info("Starting Travel Router application...")
    app = TravelRouterApp()
    try:
        app.run(None)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
    finally:
        logger.info("Application exited")

if __name__ == '__main__':
    main()
