"""Core application configuration and logging setup"""

import logging
import sys
import dbus.mainloop.glib

# Application constants
APP_NAME = "Travel Shield"
APP_ID = "com.travelrouter.app"
LOG_FILE = "travel_router_debug.log"

def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('TravelRouter')

def initialize_dbus():
    """Initialize D-Bus main loop"""
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

# Create logger instance
logger = setup_logging()
