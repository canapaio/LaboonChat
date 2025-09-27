"""
Advanced Authentication System for LaboonChat
Provides multi-factor authentication for administrative and moderation functions.

This system implements:
- Role-based access control (user, moderator, admin)
- Multi-factor authentication (password + token/file)
- Time-limited admin sessions
- Audit logging for sensitive operations
- Hardware token support (optional)
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

@dataclass
class AdminUser:
    """Advanced user with administrative privileges"""
    username: str
    display_name: str
    role: str  # 'user', 'moderator', 'admin'
    password_hash: str
    salt: str
    auth_file_hash: Optional[str] = None  # Hash of authentication file
    hardware_token_id: Optional[str] = None  # Hardware token identifier
    created_at: datetime = None
    last_login: datetime = None
    login_count: int = 0
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.permissions is None:
            self.permissions = self._get_default_permissions()
    
    def _get_default_permissions(self) -> List[str]:
        """Get default permissions based on role"""
        if self.role == 'admin':
            return [
                'user_management', 'system_config', 'plugin_management',
                'security_config', 'audit_logs', 'network_config',
                'moderation', 'content_management'
            ]
        elif self.role == 'moderator':
            return [
                'moderation', 'content_management', 'user_reports',
                'chat_management'
            ]
        else:  # user
            return ['basic_access']
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

@dataclass
class AdminSession:
    """Administrative session with time limits"""
    session_id: str
    username: str
    role: str
    created_at: datetime
    expires_at: datetime
    permissions: List[str]
    ip_address: str
    user_agent: str
    mfa_verified: bool = False
    
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        return datetime.now() < self.expires_at and self.mfa_verified
    
    def extend_session(self, minutes: int = 30):
        """Extend session expiration"""
        self.expires_at = datetime.now() + timedelta(minutes=minutes)

class AdvancedAuth:
    """Advanced authentication system for administrative functions"""
    
    def __init__(self, auth_dir: str = "auth_data"):
        self.auth_dir = Path(auth_dir)
        self.auth_dir.mkdir(exist_ok=True)
        
        # Separate directories for different auth levels
        self.admin_dir = self.auth_dir / "admin"
        self.tokens_dir = self.auth_dir / "tokens"
        self.sessions_dir = self.auth_dir / "sessions"
        
        for dir_path in [self.admin_dir, self.tokens_dir, self.sessions_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Active sessions
        self.active_sessions: Dict[str, AdminSession] = {}
        
        # Load existing admin users
        self._load_admin_users()
        
        logger.info("🔐 Advanced Authentication System initialized")
    
    def _load_admin_users(self):
        """Load existing admin users from disk"""
        self.admin_users: Dict[str, AdminUser] = {}
        
        for user_file in self.admin_dir.glob("*.json"):
            try:
                with open(user_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data and data['created_at']:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'last_login' in data and data['last_login']:
                    data['last_login'] = datetime.fromisoformat(data['last_login'])
                if 'locked_until' in data and data['locked_until']:
                    data['locked_until'] = datetime.fromisoformat(data['locked_until'])
                
                admin_user = AdminUser(**data)
                self.admin_users[admin_user.username] = admin_user
                
            except Exception as e:
                logger.error(f"Failed to load admin user from {user_file}: {e}")
    
    def _save_admin_user(self, admin_user: AdminUser):
        """Save admin user to disk"""
        try:
            user_file = self.admin_dir / f"{admin_user.username}.json"
            
            # Convert datetime objects to strings for JSON serialization
            data = asdict(admin_user)
            if data['created_at']:
                data['created_at'] = data['created_at'].isoformat()
            if data['last_login']:
                data['last_login'] = data['last_login'].isoformat()
            if data['locked_until']:
                data['locked_until'] = data['locked_until'].isoformat()
            
            with open(user_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save admin user {admin_user.username}: {e}")
    
    def _hash_password(self, password: str, salt: bytes = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32)
        
        # Use PBKDF2 with SHA256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            salt_bytes = base64.b64decode(salt.encode())
            expected_hash, _ = self._hash_password(password, salt_bytes)
            return expected_hash == password_hash
        except Exception:
            return False
    
    def _hash_file(self, file_path: str) -> str:
        """Generate hash of authentication file"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            return hashlib.sha256(file_content).hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash file {file_path}: {e}")
            return ""
    
    def create_admin_user(self, username: str, password: str, display_name: str, 
                         role: str = 'moderator', auth_file_path: str = None) -> Optional[AdminUser]:
        """Create new admin user with optional authentication file"""
        if username in self.admin_users:
            logger.warning(f"Admin user {username} already exists")
            return None
        
        if role not in ['moderator', 'admin']:
            logger.error(f"Invalid role: {role}")
            return None
        
        # Hash password
        password_hash, salt = self._hash_password(password)
        
        # Hash authentication file if provided
        auth_file_hash = None
        if auth_file_path and os.path.exists(auth_file_path):
            auth_file_hash = self._hash_file(auth_file_path)
        
        # Create admin user
        admin_user = AdminUser(
            username=username,
            display_name=display_name,
            role=role,
            password_hash=password_hash,
            salt=salt,
            auth_file_hash=auth_file_hash
        )
        
        # Save to disk and memory
        self.admin_users[username] = admin_user
        self._save_admin_user(admin_user)
        
        logger.info(f"✅ Created admin user: {username} ({role})")
        return admin_user
    
    def authenticate_admin(self, username: str, password: str, 
                          auth_file_path: str = None) -> Optional[AdminUser]:
        """Authenticate admin user with password and optional auth file"""
        if username not in self.admin_users:
            logger.warning(f"Admin user {username} not found")
            return None
        
        admin_user = self.admin_users[username]
        
        # Check if account is locked
        if admin_user.is_locked():
            logger.warning(f"Admin account {username} is locked until {admin_user.locked_until}")
            return None
        
        # Verify password
        if not self._verify_password(password, admin_user.password_hash, admin_user.salt):
            admin_user.failed_attempts += 1
            
            # Lock account after 3 failed attempts
            if admin_user.failed_attempts >= 3:
                admin_user.locked_until = datetime.now() + timedelta(minutes=30)
                logger.warning(f"🔒 Admin account {username} locked due to failed attempts")
            
            self._save_admin_user(admin_user)
            return None
        
        # Verify authentication file if required
        if admin_user.auth_file_hash:
            if not auth_file_path or not os.path.exists(auth_file_path):
                logger.warning(f"Authentication file required for {username}")
                return None
            
            file_hash = self._hash_file(auth_file_path)
            if file_hash != admin_user.auth_file_hash:
                logger.warning(f"Invalid authentication file for {username}")
                admin_user.failed_attempts += 1
                self._save_admin_user(admin_user)
                return None
        
        # Authentication successful
        admin_user.failed_attempts = 0
        admin_user.last_login = datetime.now()
        admin_user.login_count += 1
        self._save_admin_user(admin_user)
        
        logger.info(f"✅ Admin {username} authenticated successfully")
        return admin_user
    
    def create_admin_session(self, admin_user: AdminUser, ip_address: str, 
                           user_agent: str, duration_minutes: int = 60) -> AdminSession:
        """Create administrative session"""
        session_id = secrets.token_urlsafe(32)
        
        session = AdminSession(
            session_id=session_id,
            username=admin_user.username,
            role=admin_user.role,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=duration_minutes),
            permissions=admin_user.permissions,
            ip_address=ip_address,
            user_agent=user_agent,
            mfa_verified=True  # Set to True after successful auth
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f"🎫 Created admin session for {admin_user.username} (expires in {duration_minutes}m)")
        return session
    
    def verify_admin_session(self, session_id: str) -> Optional[AdminSession]:
        """Verify and return admin session if valid"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        if not session.is_valid():
            # Remove expired session
            del self.active_sessions[session_id]
            logger.info(f"🕐 Admin session {session_id} expired")
            return None
        
        return session
    
    def revoke_admin_session(self, session_id: str) -> bool:
        """Revoke admin session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            del self.active_sessions[session_id]
            logger.info(f"🚫 Revoked admin session for {session.username}")
            return True
        return False
    
    def extend_admin_session(self, session_id: str, minutes: int = 30) -> bool:
        """Extend admin session"""
        session = self.verify_admin_session(session_id)
        if session:
            session.extend_session(minutes)
            logger.info(f"⏰ Extended admin session for {session.username} by {minutes}m")
            return True
        return False
    
    def get_admin_user(self, username: str) -> Optional[AdminUser]:
        """Get admin user by username"""
        return self.admin_users.get(username)
    
    def list_admin_users(self) -> List[AdminUser]:
        """List all admin users"""
        return list(self.admin_users.values())
    
    def update_admin_permissions(self, username: str, permissions: List[str]) -> bool:
        """Update admin user permissions"""
        if username not in self.admin_users:
            return False
        
        admin_user = self.admin_users[username]
        admin_user.permissions = permissions
        self._save_admin_user(admin_user)
        
        logger.info(f"📝 Updated permissions for {username}: {permissions}")
        return True
    
    def delete_admin_user(self, username: str) -> bool:
        """Delete admin user"""
        if username not in self.admin_users:
            return False
        
        # Remove from memory
        del self.admin_users[username]
        
        # Remove file
        user_file = self.admin_dir / f"{username}.json"
        if user_file.exists():
            user_file.unlink()
        
        # Revoke all sessions for this user
        sessions_to_revoke = [
            sid for sid, session in self.active_sessions.items()
            if session.username == username
        ]
        for sid in sessions_to_revoke:
            self.revoke_admin_session(sid)
        
        logger.info(f"🗑️ Deleted admin user: {username}")
        return True

# Global instance
_advanced_auth = None

def get_advanced_auth() -> AdvancedAuth:
    """Get global advanced auth instance"""
    global _advanced_auth
    if _advanced_auth is None:
        _advanced_auth = AdvancedAuth()
    return _advanced_auth

# Convenience functions
def create_admin_user(username: str, password: str, display_name: str, 
                     role: str = 'moderator', auth_file_path: str = None) -> Optional[AdminUser]:
    """Create admin user"""
    return get_advanced_auth().create_admin_user(username, password, display_name, role, auth_file_path)

def authenticate_admin(username: str, password: str, auth_file_path: str = None) -> Optional[AdminUser]:
    """Authenticate admin user"""
    return get_advanced_auth().authenticate_admin(username, password, auth_file_path)

def verify_admin_session(session_id: str) -> Optional[AdminSession]:
    """Verify admin session"""
    return get_advanced_auth().verify_admin_session(session_id)

def require_admin_permission(permission: str):
    """Decorator to require admin permission"""
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            # Get session from request
            session_id = request.cookies.get('admin_session')
            if not session_id:
                return web.json_response({'error': 'Admin authentication required'}, status=401)
            
            session = verify_admin_session(session_id)
            if not session:
                return web.json_response({'error': 'Invalid or expired admin session'}, status=401)
            
            if permission not in session.permissions:
                return web.json_response({'error': f'Permission {permission} required'}, status=403)
            
            # Add session to request for handler use
            request['admin_session'] = session
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the advanced auth system
    auth = AdvancedAuth()
    
    # Create test admin
    admin = auth.create_admin_user(
        username="admin",
        password="secure_admin_password",
        display_name="System Administrator",
        role="admin"
    )
    
    if admin:
        print(f"✅ Created admin: {admin.username} with permissions: {admin.permissions}")
        
        # Test authentication
        authenticated = auth.authenticate_admin("admin", "secure_admin_password")
        if authenticated:
            print(f"✅ Authentication successful for {authenticated.username}")
            
            # Create session
            session = auth.create_admin_session(authenticated, "127.0.0.1", "Test Agent")
            print(f"✅ Created session: {session.session_id}")
            
            # Verify session
            verified = auth.verify_admin_session(session.session_id)
            if verified:
                print(f"✅ Session verified: {verified.username} ({verified.role})")
        else:
            print("❌ Authentication failed")
    else:
        print("❌ Failed to create admin user")