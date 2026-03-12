## PROJECT STILL UNDER DEVELOPMENT 
First personal github project! Though I'm not making it for the sake of a project. I lowkey hate public captive portals.

Quick Summary:
Travel Shield = VPN Router for your devices

   1. You connect to hotel WiFi + activate VPN on laptop
   2. App creates a virtual WiFi interface (wlo1_ap) on your laptop
   3. App broadcasts a secure hotspot with WPA2 encryption
   4. Your devices connect to this hotspot (phone, tablet, etc.)
   5. Traffic flows: Device → Laptop Hotspot → VPN Tunnel → Internet
   6. Result: All your devices protected through ONE VPN connection! 



## Credits

Built with:
- Python 3.12+
- Claude Sonnet 4.5
- GTK 4
- NetworkManager
- python-networkmanager
- cryptography
- keyring
