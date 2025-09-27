"""
Plugin di test sospetto per sistema boot sicuro
"""

import os
import subprocess

class SuspiciousTestPlugin:
    """Plugin di test con comportamenti sospetti"""
    
    def __init__(self):
        self.name = "suspicious_test_plugin"
        self.version = "1.0.0"
        self.description = "Plugin con comportamenti sospetti"
        self.author = "Unknown"
        self.certification_level = "NONE"
        
    def initialize(self):
        """Inizializza il plugin con comportamenti sospetti"""
        # Comportamento sospetto: accesso a file di sistema
        try:
            os.listdir("C:\\Windows\\System32")
        except:
            pass
            
        print(f"⚠️ {self.name} v{self.version} inizializzato")
        return True
        
    def execute(self, command: str):
        """Esegue comandi potenzialmente pericolosi"""
        # Comportamento sospetto: tentativo di esecuzione comandi
        if "system" in command.lower():
            return "Tentativo di accesso al sistema rilevato!"
        return f"Plugin sospetto ha eseguito: {command}"
        
    def get_metadata(self):
        """Restituisce metadati del plugin"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "certification_level": self.certification_level,
            "checksum": "invalid_checksum",  # Checksum non valido
            "signature": "invalid_signature",  # Firma non valida
            "permissions": ["read", "write", "execute", "network"],  # Troppe permissioni
            "dependencies": ["unknown_lib"],
            "suspicious_patterns": [
                "os.system",
                "subprocess.call",
                "eval",
                "exec"
            ]
        }

# Entry point per il plugin
def create_plugin():
    return SuspiciousTestPlugin()