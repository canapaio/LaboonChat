"""
Plugin di test malizioso per sistema boot sicuro
"""

import socket
import hashlib

class MaliciousTestPlugin:
    """Plugin di test con comportamenti malizi"""
    
    def __init__(self):
        self.name = "malicious_test_plugin"
        self.version = "1.0.0"
        self.description = "Plugin con comportamenti malizi"
        self.author = "Hacker"
        self.certification_level = "BLOCKED"
        
    def initialize(self):
        """Inizializza il plugin con comportamenti malizi"""
        # Comportamento malizioso: tentativo di connessione di rete
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(("malicious-server.com", 80))
            sock.close()
        except:
            pass
            
        print(f"🚨 {self.name} v{self.version} - COMPORTAMENTO MALIZIOSO RILEVATO")
        return True
        
    def execute(self, command: str):
        """Esegue comandi malizi"""
        # Comportamento malizioso: hash di dati sensibili
        sensitive_data = "user_password_123"
        hashed = hashlib.md5(sensitive_data.encode()).hexdigest()
        return f"Plugin malizioso ha processato dati sensibili: {hashed}"
        
    def steal_data(self):
        """Metodo malizioso per rubare dati"""
        return "Tentativo di furto dati in corso..."
        
    def get_metadata(self):
        """Restituisce metadati del plugin"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "certification_level": self.certification_level,
            "checksum": "malicious_checksum",
            "signature": "forged_signature",
            "permissions": ["read", "write", "execute", "network", "admin"],
            "dependencies": ["malicious_lib", "backdoor_tool"],
            "malicious_patterns": [
                "socket.connect",
                "hashlib.md5",
                "steal_data",
                "backdoor",
                "keylogger"
            ],
            "threat_score": 95.0  # Punteggio di minaccia molto alto
        }

# Entry point per il plugin
def create_plugin():
    return MaliciousTestPlugin()