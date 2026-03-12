"""GTK4 GUI Application"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import threading

from ..core import APP_NAME, APP_ID, logger
from ..network import NetworkDetector, HotspotManager, RoutingManager


class TravelRouterApp(Gtk.Application):
    """Main GTK application for Travel Shield VPN Router"""
    
    def __init__(self):
        super().__init__(application_id=APP_ID)
        
        # Initialize components
        self.network_detector = NetworkDetector()
        self.hotspot_manager = HotspotManager()
        self.hotspot_process = None
        
        logger.info("TravelRouterApp initialized")
        
        # Connect shutdown signal
        self.connect('shutdown', self.on_shutdown)
    
    def do_activate(self):
        """Activate the application and create the main window"""
        logger.info("Application activating...")
        
        win = Gtk.ApplicationWindow(application=self)
        win.set_title(APP_NAME)
        win.set_default_size(400, 300)
        win.connect('close-request', self.on_window_close_request)
        
        # Build UI
        self._build_ui(win)
        
        win.present()
        logger.info("Window presented, checking initial status...")
        
        # Check initial status
        GLib.timeout_add(100, self.check_status)
    
    def _build_ui(self, win):
        """Build the user interface"""
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        # Title
        title = Gtk.Label()
        title.set_markup(f"<span size='x-large' weight='bold'>{APP_NAME}</span>")
        box.append(title)
        
        # Status section
        self._add_status_section(box)
        
        # Configuration section
        self._add_config_section(box)
        
        # Control buttons
        self._add_control_buttons(box)
        
        win.set_child(box)
    
    def _add_status_section(self, parent_box):
        """Add status display section"""
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
        parent_box.append(status_frame)
    
    def _add_config_section(self, parent_box):
        """Add configuration input section"""
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
        parent_box.append(config_frame)
    
    def _add_control_buttons(self, parent_box):
        """Add control buttons"""
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
        
        parent_box.append(button_box)
    
    def check_status(self):
        """Check VPN and WiFi status"""
        logger.debug("Checking VPN and WiFi status...")
        
        # Check VPN
        if self.network_detector.check_vpn_status():
            conn_id = self.network_detector.vpn_connection.Id
            self.vpn_status_label.set_markup(
                f"<span foreground='green'>✓ VPN Status: Connected ({conn_id})</span>"
            )
        else:
            self.vpn_status_label.set_markup(
                "<span foreground='red'>✗ VPN Status: Not Connected</span>"
            )
        
        # Check WiFi device
        if self.network_detector.check_wifi_device():
            wifi_iface = self.network_detector.wifi_device.Interface
            self.wifi_status_label.set_markup(
                f"<span foreground='green'>✓ WiFi Device: {wifi_iface}</span>"
            )
        else:
            self.wifi_status_label.set_markup(
                "<span foreground='red'>✗ WiFi Device: Not Found</span>"
            )
        
        logger.debug("Status check complete")
        return False
    
    def on_start_clicked(self, button):
        """Start the VPN hotspot"""
        logger.info("Start button clicked")
        
        if not self.network_detector.vpn_connection:
            logger.warning("Cannot start hotspot - no VPN connection")
            self.show_error_dialog("No VPN connection detected. Please connect to a VPN first.")
            return
        
        if not self.network_detector.wifi_device:
            logger.warning("Cannot start hotspot - no WiFi device")
            self.show_error_dialog("No WiFi device found. Cannot create hotspot.")
            return
        
        ssid = self.ssid_entry.get_text()
        password = self.pass_entry.get_text()
        
        if len(password) < 8:
            logger.warning("Password too short")
            self.show_error_dialog("Password must be at least 8 characters long.")
            return
        
        logger.info(f"Starting hotspot with SSID: {ssid}")
        
        # Start hotspot in background thread
        def start_hotspot():
            try:
                wifi_iface = self.network_detector.wifi_device.Interface
                vpn_iface = self.network_detector.get_vpn_interface()
                
                if not vpn_iface:
                    GLib.idle_add(self.show_error_dialog, 
                                "Could not determine VPN interface.")
                    GLib.idle_add(lambda: self.start_button.set_sensitive(True))
                    return
                
                logger.info(f"Creating concurrent hotspot: {wifi_iface} -> {vpn_iface}")
                
                # Create hotspot
                self.hotspot_process = self.hotspot_manager.create_concurrent_hotspot(
                    wifi_iface, ssid, password, vpn_iface
                )
                
                # Setup routing
                if not RoutingManager.setup_routing(
                    self.hotspot_process['ap_interface'], 
                    vpn_iface
                ):
                    raise Exception("Failed to setup routing")
                
                logger.info("Concurrent hotspot configured successfully")
                GLib.idle_add(self.on_hotspot_started)
                
            except Exception as e:
                logger.error(f"Failed to start hotspot: {e}", exc_info=True)
                GLib.idle_add(self.show_error_dialog, f"Failed to start hotspot: {e}")
                GLib.idle_add(lambda: self.start_button.set_sensitive(True))
        
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
            if self.hotspot_process:
                # Cleanup routing
                if isinstance(self.hotspot_process, dict):
                    ap_iface = self.hotspot_process.get('ap_interface')
                    vpn_iface = self.hotspot_process.get('vpn')
                    
                    if ap_iface and vpn_iface:
                        RoutingManager.cleanup_routing(ap_iface, vpn_iface)
                
                # Stop hotspot
                self.hotspot_manager.stop_hotspot(self.hotspot_process)
            
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
    
    def on_window_close_request(self, window):
        """Handle window close request"""
        logger.info("Window close requested")
        if self.hotspot_process:
            logger.info("Stopping hotspot before closing...")
            try:
                self.on_stop_clicked(None)
            except Exception as e:
                logger.error(f"Error stopping hotspot: {e}")
        logger.info("Closing application")
        return False
    
    def on_shutdown(self, app):
        """Cleanup on application shutdown"""
        logger.info("Application shutting down...")
        if self.hotspot_process:
            try:
                self.hotspot_manager.stop_hotspot(self.hotspot_process)
                
                if isinstance(self.hotspot_process, dict):
                    ap_iface = self.hotspot_process.get('ap_interface')
                    vpn_iface = self.hotspot_process.get('vpn')
                    if ap_iface and vpn_iface:
                        RoutingManager.cleanup_routing(ap_iface, vpn_iface)
            except Exception as e:
                logger.error(f"Error during shutdown cleanup: {e}")
        logger.info("Shutdown complete")
    
    def show_error_dialog(self, message):
        """Show an error dialog"""
        logger.error(f"Showing error dialog: {message}")
        dialog = Gtk.AlertDialog()
        dialog.set_message("Error")
        dialog.set_detail(message)
        dialog.show(self.get_active_window())
