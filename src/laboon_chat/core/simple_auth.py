"""
🔐 LaboonChat Simple Authentication - Autenticazione Semplice File-Based
========================================================================

Sistema di autenticazione semplice basato su file ID utente crittografati.
Perfetto per uso quotidiano con protezione automatica tramite rete parentale.

🐋 "Semplicità elegante per la vita quotidiana" 🌊

Features:
- File ID utente crittografati con password
- Decrittazione automatica al login
- Integrazione con sistema parental network
- Zero friction per utenti onesti
- Fallback sicuro per casi d'emergenza

Author: LaboonChat Team
License: GPL-3.0
"""

import json
import hashlib
import base64
import os
import time
from typing import Dict, Optional, Any, Tuple, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class UserIDFile:
    """Rappresenta un file ID utente crittografato"""
    
    def __init__(self, user_id: str, display_name: str, email: str = "", 
                 avatar_path: str = "", preferences: Dict[str, Any] = None):
        self.user_id = user_id
        self.display_name = display_name
        self.email = email
        self.avatar_path = avatar_path
        self.preferences = preferences or {}
        self.created_at = time.time()
        self.last_login = time.time()
        self.login_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per serializzazione"""
        return {
            'user_id': self.user_id,
            'display_name': self.display_name,
            'email': self.email,
            'avatar_path': self.avatar_path,
            'preferences': self.preferences,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'login_count': self.login_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserIDFile':
        """Crea istanza da dizionario"""
        instance = cls(
            user_id=data['user_id'],
            display_name=data['display_name'],
            email=data.get('email', ''),
            avatar_path=data.get('avatar_path', ''),
            preferences=data.get('preferences', {})
        )
        instance.created_at = data.get('created_at', time.time())
        instance.last_login = data.get('last_login', time.time())
        instance.login_count = data.get('login_count', 0)
        return instance
    
    def update_login(self):
        """Aggiorna statistiche di login"""
        self.last_login = time.time()
        self.login_count += 1

class SimpleAuthCrypto:
    """Gestisce crittografia per file ID utente"""
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Deriva chiave crittografica da password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    @staticmethod
    def encrypt_user_data(user_data: Dict[str, Any], password: str) -> Tuple[bytes, bytes]:
        """Crittografa dati utente con password"""
        # Genera salt casuale
        salt = os.urandom(16)
        
        # Deriva chiave da password
        key = SimpleAuthCrypto.derive_key_from_password(password, salt)
        
        # Crittografa dati
        fernet = Fernet(key)
        json_data = json.dumps(user_data).encode()
        encrypted_data = fernet.encrypt(json_data)
        
        return encrypted_data, salt
    
    @staticmethod
    def decrypt_user_data(encrypted_data: bytes, salt: bytes, password: str) -> Optional[Dict[str, Any]]:
        """Decrittografa dati utente con password"""
        try:
            # Deriva chiave da password
            key = SimpleAuthCrypto.derive_key_from_password(password, salt)
            
            # Decrittografa dati
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse JSON
            return json.loads(decrypted_data.decode())
        
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

class SimpleAuth:
    """Sistema di autenticazione semplice basato su file ID"""
    
    def __init__(self, users_dir: str = "users"):
        self.users_dir = Path(users_dir)
        self.users_dir.mkdir(exist_ok=True)
        
        # Cache utenti attivi
        self.active_users: Dict[str, UserIDFile] = {}
        self.session_tokens: Dict[str, str] = {}  # token -> user_id
        
        logger.info(f"SimpleAuth initialized with users dir: {self.users_dir}")
    
    def _get_user_file_path(self, user_id: str) -> Path:
        """Ottieni percorso file per user ID"""
        # Usa hash dell'user_id per nome file sicuro
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        return self.users_dir / f"{user_hash}.laboon"
    
    def create_user_id_file(self, user_id: str, display_name: str, password: str,
                           email: str = "", avatar_path: str = "", 
                           preferences: Dict[str, Any] = None) -> bool:
        """Crea nuovo file ID utente crittografato"""
        try:
            # Controlla se utente già exists
            if self.user_exists(user_id):
                logger.warning(f"User {user_id} already exists")
                return False
            
            # Crea oggetto utente
            user_file = UserIDFile(
                user_id=user_id,
                display_name=display_name,
                email=email,
                avatar_path=avatar_path,
                preferences=preferences
            )
            
            # Crittografa e salva
            encrypted_data, salt = SimpleAuthCrypto.encrypt_user_data(
                user_file.to_dict(), password
            )
            
            # Salva file con salt + dati crittografati
            file_path = self._get_user_file_path(user_id)
            with open(file_path, 'wb') as f:
                f.write(salt)  # Primi 16 bytes = salt
                f.write(encrypted_data)  # Resto = dati crittografati
            
            logger.info(f"Created user ID file for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user ID file: {e}")
            return False
    
    def authenticate_user(self, user_id: str, password: str) -> Optional[UserIDFile]:
        """Autentica utente con password e carica file ID"""
        try:
            file_path = self._get_user_file_path(user_id)
            
            if not file_path.exists():
                logger.warning(f"User file not found for {user_id}")
                return None
            
            # Leggi file
            with open(file_path, 'rb') as f:
                salt = f.read(16)  # Primi 16 bytes = salt
                encrypted_data = f.read()  # Resto = dati crittografati
            
            # Decrittografa
            user_data = SimpleAuthCrypto.decrypt_user_data(encrypted_data, salt, password)
            
            if user_data is None:
                logger.warning(f"Authentication failed for {user_id}")
                return None
            
            # Crea oggetto utente
            user_file = UserIDFile.from_dict(user_data)
            user_file.update_login()
            
            # Aggiorna file con nuovo login
            self._update_user_file(user_file, password)
            
            # Aggiungi a cache utenti attivi
            self.active_users[user_id] = user_file
            
            logger.info(f"User {user_id} authenticated successfully")
            return user_file
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def _update_user_file(self, user_file: UserIDFile, password: str):
        """Aggiorna file utente con nuovi dati"""
        try:
            encrypted_data, salt = SimpleAuthCrypto.encrypt_user_data(
                user_file.to_dict(), password
            )
            
            file_path = self._get_user_file_path(user_file.user_id)
            with open(file_path, 'wb') as f:
                f.write(salt)
                f.write(encrypted_data)
                
        except Exception as e:
            logger.error(f"Error updating user file: {e}")
    
    def user_exists(self, user_id: str) -> bool:
        """Controlla se utente esiste"""
        file_path = self._get_user_file_path(user_id)
        return file_path.exists()
    
    def generate_session_token(self, user_id: str) -> str:
        """Genera token di sessione per utente autenticato"""
        # Token semplice basato su timestamp + user_id
        token_data = f"{user_id}:{time.time()}:{os.urandom(8).hex()}"
        token = base64.urlsafe_b64encode(token_data.encode()).decode()
        
        self.session_tokens[token] = user_id
        logger.debug(f"Generated session token for {user_id}")
        return token
    
    def validate_session_token(self, token: str) -> Optional[str]:
        """Valida token di sessione e ritorna user_id"""
        if token in self.session_tokens:
            user_id = self.session_tokens[token]
            
            # Controlla se utente è ancora attivo
            if user_id in self.active_users:
                return user_id
        
        return None
    
    def logout_user(self, user_id: str):
        """Logout utente e rimuovi da cache"""
        # Rimuovi da utenti attivi
        if user_id in self.active_users:
            del self.active_users[user_id]
        
        # Rimuovi token di sessione
        tokens_to_remove = [
            token for token, uid in self.session_tokens.items() 
            if uid == user_id
        ]
        for token in tokens_to_remove:
            del self.session_tokens[token]
        
        logger.info(f"User {user_id} logged out")
    
    def get_active_user(self, user_id: str) -> Optional[UserIDFile]:
        """Ottieni utente attivo dalla cache"""
        return self.active_users.get(user_id)
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any], 
                               password: str) -> bool:
        """Aggiorna preferenze utente"""
        try:
            user_file = self.active_users.get(user_id)
            if not user_file:
                logger.warning(f"User {user_id} not active")
                return False
            
            # Aggiorna preferenze
            user_file.preferences.update(preferences)
            
            # Salva file aggiornato
            self._update_user_file(user_file, password)
            
            logger.info(f"Updated preferences for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return False
    
    def list_users(self) -> List[str]:
        """Lista tutti gli user ID disponibili (per debug)"""
        user_files = list(self.users_dir.glob("*.laboon"))
        return [f.stem for f in user_files]
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche sistema autenticazione"""
        total_users = len(list(self.users_dir.glob("*.laboon")))
        active_users = len(self.active_users)
        active_sessions = len(self.session_tokens)
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'active_sessions': active_sessions,
            'users_dir': str(self.users_dir)
        }

# Singleton instance
_simple_auth_instance = None

def get_simple_auth() -> SimpleAuth:
    """Ottieni istanza singleton del sistema di autenticazione semplice"""
    global _simple_auth_instance
    if _simple_auth_instance is None:
        _simple_auth_instance = SimpleAuth()
    return _simple_auth_instance

# Convenience functions
def create_user(user_id: str, display_name: str, password: str, **kwargs) -> bool:
    """Crea nuovo utente"""
    auth = get_simple_auth()
    return auth.create_user_id_file(user_id, display_name, password, **kwargs)

def login_user(user_id: str, password: str) -> Optional[str]:
    """Login utente e ritorna token di sessione"""
    auth = get_simple_auth()
    user_file = auth.authenticate_user(user_id, password)
    if user_file:
        return auth.generate_session_token(user_id)
    return None

def validate_token(token: str) -> Optional[str]:
    """Valida token e ritorna user_id"""
    auth = get_simple_auth()
    return auth.validate_session_token(token)

def logout_user(user_id: str):
    """Logout utente"""
    auth = get_simple_auth()
    auth.logout_user(user_id)

if __name__ == "__main__":
    # Test del sistema
    def test_simple_auth():
        print("🔐 Testing Simple Authentication...")
        
        auth = SimpleAuth("test_users")
        
        # Crea utente test
        success = auth.create_user_id_file(
            user_id="test_user",
            display_name="Test User",
            password="test_password",
            email="test@example.com",
            preferences={"theme": "dark", "language": "it"}
        )
        print(f"✅ User creation: {success}")
        
        # Test autenticazione
        user_file = auth.authenticate_user("test_user", "test_password")
        if user_file:
            print(f"✅ Authentication successful: {user_file.display_name}")
            
            # Genera token
            token = auth.generate_session_token("test_user")
            print(f"✅ Session token: {token[:20]}...")
            
            # Valida token
            validated_user = auth.validate_session_token(token)
            print(f"✅ Token validation: {validated_user}")
            
            # Aggiorna preferenze
            success = auth.update_user_preferences(
                "test_user", 
                {"new_setting": "value"}, 
                "test_password"
            )
            print(f"✅ Preferences update: {success}")
        
        # Test password sbagliata
        wrong_auth = auth.authenticate_user("test_user", "wrong_password")
        print(f"✅ Wrong password test: {wrong_auth is None}")
        
        # Statistiche
        stats = auth.get_user_stats()
        print(f"📊 Auth stats: {stats}")
        
        print("🔐 Simple Authentication test completed!")
    
    test_simple_auth()