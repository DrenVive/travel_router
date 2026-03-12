#!/usr/bin/env python3
"""
Travel Shield VPN Router - Main Entry Point

A GTK4 application that creates a WiFi hotspot routing through your VPN connection.
Designed for secure internet access while traveling.
"""

import sys
from src.core import initialize_dbus, logger
from src.ui import TravelRouterApp


def main():
    """Main entry point for the application"""
    try:
        # Initialize D-Bus
        initialize_dbus()
        logger.info("D-Bus main loop initialized")
        
        # Create and run the application
        logger.info("Starting Travel Shield VPN Router...")
        app = TravelRouterApp()
        app.run(None)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application exited")


if __name__ == '__main__':
    main()
