from cryptography.fernet import Fernet
import keyring
import json
import os

class ConfigHandler:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.service_name = 'travel_router'
        self.key_name = 'encryption_key'

    def _get_or_create_key(self):
        """Get encryption key from system keyring or create new one"""
        # Try to get key from system keyring
        key = keyring.get_password(self.service_name, self.key_name)
        
        if key:
            return key.encode()
        else:
            # Generate new key and store in keyring
            key = Fernet.generate_key()
            keyring.set_password(self.service_name, self.key_name, key.decode())
            return key
        
    def load_config(self):
        """Load and decrypt configuration"""
        key = self._get_or_create_key()
        cipher = Fernet(key)

        with open(self.config_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())

    def save_config(self, config):
        """Encrypt and save configuration"""
        key = self._get_or_create_key()
        cipher = Fernet(key)

        encrypted_data = cipher.encrypt(json.dumps(config).encode())

        with open(self.config_file, 'wb') as f:
            f.write(encrypted_data)

        os.chmod(self.config_file, 0o600)