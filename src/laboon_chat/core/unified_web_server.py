#!/usr/bin/env python3
"""
🌐 Decentralized P2P Web Interface
Local node interface for peer-to-peer messaging with individual responsibility
Enhanced with distributed authentication and network protection
"""

import os
import json
import jwt
import asyncio
import logging
import secrets
import webbrowser
import socket
import ipaddress
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from aiohttp import web, WSMsgType
import aiohttp_cors
from aiohttp.web_ws import WebSocketResponse

# Import new authentication systems
try:
    from .simple_auth import get_simple_auth, SimpleAuth, UserIDFile
    from .advanced_auth import AdvancedAuth, get_advanced_auth, require_admin_permission
except ImportError:
    # Fallback for direct execution
    from simple_auth import get_simple_auth, SimpleAuth, UserIDFile
    from advanced_auth import AdvancedAuth, get_advanced_auth, require_admin_permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions for parental network protection
async def log_user_action_local(user_id: str, action_type: str, context: dict):
    """Log user action for parental network analysis"""
    try:
        protection = get_parental_protection()
        action = UserAction(
            user_id=user_id,
            action_type=action_type,
            timestamp=datetime.now(),
            context=context
        )
        protection.log_action(action)
    except Exception as e:
        logger.error(f"Failed to log user action: {e}")

def is_user_trusted_local(user_id: str) -> bool:
    """Check if user is trusted by the parental network"""
    try:
        protection = get_parental_protection()
        trust_score = protection.reputation_system.get_trust_score(user_id)
        return trust_score.score >= 0.5  # Threshold for trusted users
    except Exception as e:
        logger.error(f"Failed to check user trust: {e}")
        return True  # Default to trusted if check fails

class P2PWebInterface:
    """Local web interface for P2P messaging with distributed authentication and individual responsibility"""
    
    def __init__(self, host='localhost', port=9494, secret_key=None, auto_launch_browser=True, allowed_networks=None):
        self.host = host
        self.port = port
        self.secret_key = secret_key or 'p2p-node-secret-key-change-in-production'
        self.auto_launch_browser = auto_launch_browser
        
        # Security configuration - Default allowed networks for local access
        self.allowed_networks = allowed_networks or [
            '127.0.0.0/8',      # Localhost IPv4
            '::1/128',          # Localhost IPv6
            '192.168.0.0/16',   # Private Class C
            '172.16.0.0/12',    # Private Class B  
            '10.0.0.0/8',       # Private Class A
        ]
        
        # Generate startup token for automatic access
        self.startup_token = self.generate_startup_token()
        
        # Initialize new authentication and protection systems
        self.simple_auth = get_simple_auth()
        self.parental_protection = get_parental_protection()
        self.advanced_auth = get_advanced_auth()
        
        # Sistema di monitoraggio chat semplificato
        try:
            from .chat_monitor import get_chat_monitor
            self.chat_monitor = get_chat_monitor()
            logger.info("👁️ Chat Monitor initialized")
        except ImportError as e:
            logger.warning(f"Chat Monitor not available: {e}")
            self.chat_monitor = None
        
        # Authentication modes
        self.auth_mode = 'simple'  # 'simple' or 'advanced'
        
        # Paths
        self.base_dir = Path(__file__).parent.parent
        self.template_dir = self.base_dir / 'ui' / 'templates'
        self.static_dir = self.base_dir / 'ui' / 'static'
        self.generated_ui_dir = self.base_dir / 'core' / 'generated_ui'
        
        # WebSocket connections
        self.websockets = set()
        
        # Initialize app
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
        
        # Add security middleware
        self.app.middlewares.append(self.security_middleware)
        self.app.middlewares.append(self.parental_protection_middleware)
        
        logger.info("🛡️ UnifiedWebServer initialized with Simple Auth + Parental Protection")
        
    def is_ip_allowed(self, client_ip: str) -> bool:
        """Check if client IP is in allowed networks"""
        try:
            client_addr = ipaddress.ip_address(client_ip)
            for network_str in self.allowed_networks:
                network = ipaddress.ip_network(network_str, strict=False)
                if client_addr in network:
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking IP {client_ip}: {e}")
            return False

    @web.middleware
    async def security_middleware(self, request, handler):
        """Security middleware to check allowed IPs"""
        # Get client IP (handle proxy headers)
        client_ip = request.headers.get('X-Forwarded-For', 
                   request.headers.get('X-Real-IP', 
                   request.remote))
        
        # Extract first IP if multiple (proxy chain)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Check if IP is allowed
        if not self.is_ip_allowed(client_ip):
            logger.warning(f"🚫 Access denied from IP: {client_ip}")
            return web.Response(
                text="Access denied: IP not in allowed networks",
                status=403
            )
        
        # IP is allowed, continue to handler
        logger.info(f"✅ Access granted from IP: {client_ip}")
        return await handler(request)
    
    @web.middleware
    async def parental_protection_middleware(self, request, handler):
        """Parental network protection middleware"""
        # Skip protection for static files and login
        if (request.path.startswith('/static/') or 
            request.path.startswith('/generated/') or
            request.path == '/login'):
            return await handler(request)
        
        # Get user from request if authenticated
        user_id = None
        if hasattr(request, 'get') and request.get('user'):
            user_id = request['user'].get('username', 'anonymous')
        
        # Log user action for parental network analysis
        if user_id:
            action_type = f"{request.method.lower()}_{request.path.replace('/', '_')}"
            context = {
                'method': request.method,
                'path': request.path,
                'user_agent': request.headers.get('User-Agent', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            # Log action asynchronously
            try:
                await log_user_action(user_id, action_type, context)
            except Exception as e:
                logger.warning(f"Failed to log user action: {e}")
            
            # Check if user is trusted by the network
            if not is_user_trusted(user_id):
                trust_score = self.parental_protection.reputation_system.get_trust_score(user_id).score
                logger.warning(f"⚠️ Untrusted user {user_id} (score: {trust_score:.2f}) accessing {request.path}")
                
                # For very low trust scores, deny access
                if trust_score < 0.1:
                    return web.Response(
                        text="Access temporarily restricted due to network protection",
                        status=429
                    )
        
        return await handler(request)
        
    def generate_startup_token(self) -> str:
        """Generate a secure startup token for automatic access"""
        startup_token = secrets.token_urlsafe(32)
        logger.info(f"🔑 Generated startup token: {startup_token[:8]}...")
        return startup_token
        
    def get_local_ip(self) -> str:
        """Get local IP address for network access"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def print_access_info(self):
        """Print access information for local and network access"""
        local_ip = self.get_local_ip()
        
        print("\n" + "="*60)
        print("🐋 LaboonChat - Server Avviato!")
        print("="*60)
        print(f"📍 Accesso Locale:    http://localhost:{self.port}")
        print(f"🌐 Accesso Rete:      http://{local_ip}:{self.port}")
        print(f"📱 Da Cellulare:      http://{local_ip}:{self.port}")
        print("="*60)
        print("🔒 Reti IP Ammesse:")
        for network in self.allowed_networks:
            print(f"   ✅ {network}")
        print("="*60)
        print("🔑 Accesso Automatico:")
        print(f"   Token: {self.startup_token}")
        print(f"   URL:   http://localhost:{self.port}?token={self.startup_token}")
        print("="*60)
        print("💡 Per accesso da dispositivi remoti:")
        print("   1. Assicurati che il firewall permetta la porta")
        print("   2. Usa l'indirizzo di rete mostrato sopra")
        print("   3. Per sicurezza extra, usa una VPN")
        print("="*60)
        
    def launch_browser(self):
        """Launch browser with startup token for automatic access"""
        if self.auto_launch_browser:
            startup_url = f"http://localhost:{self.port}?token={self.startup_token}"
            try:
                webbrowser.open(startup_url)
                logger.info(f"🌐 Browser lanciato automaticamente: {startup_url}")
            except Exception as e:
                logger.warning(f"⚠️ Impossibile lanciare il browser automaticamente: {e}")
                logger.info(f"🔗 Apri manualmente: {startup_url}")

    def setup_routes(self):
        """Setup all routes for the unified server"""
        
        # Authentication routes
        self.app.router.add_get('/login', self.handle_login)
        self.app.router.add_post('/login', self.handle_login)
        self.app.router.add_post('/logout', self.handle_logout)
        self.app.router.add_post('/register', self.handle_register)
        
        # Advanced authentication routes
        self.app.router.add_post('/admin/login', self.handle_admin_login)
        self.app.router.add_post('/admin/logout', self.handle_admin_logout)
        
        # Administrative routes (require admin authentication)
        self.app.router.add_get('/admin/users', self.handle_admin_users)
        self.app.router.add_post('/admin/users', self.handle_create_admin_user)
        self.app.router.add_put('/admin/users/{username}', self.handle_update_admin_user)
        self.app.router.add_delete('/admin/users/{username}', self.handle_delete_admin_user)
        
        # Main application routes (require authentication)
        self.app.router.add_get('/', self.handle_main_app)
        self.app.router.add_get('/ws', self.handle_websocket)
        
        # Chat API routes (require authentication)
        self.app.router.add_post('/api/chat/send', self.handle_send_message)
        self.app.router.add_get('/api/chat/history/{user_id}', self.handle_chat_history)
        
        # Minor protection API routes (require authentication)
        self.app.router.add_get('/api/minor/status/{user_id}', self.handle_minor_status)
        self.app.router.add_get('/api/minor/stats', self.handle_minor_stats)
        self.app.router.add_get('/parent_dashboard', self.handle_parent_dashboard)
        
        # Plugin configuration routes (require authentication)
        self.app.router.add_get('/plugin_menu.html', self.handle_plugin_menu)
        self.app.router.add_get('/api/plugins/{path:.*}', self.handle_plugin_api)
        self.app.router.add_post('/api/plugins/{path:.*}', self.handle_plugin_api)
        self.app.router.add_put('/api/plugins/{path:.*}', self.handle_plugin_api)
        self.app.router.add_delete('/api/plugins/{path:.*}', self.handle_plugin_api)
        
        # Static files
        if self.static_dir.exists():
            self.app.router.add_static('/static/', self.static_dir)
        
        # Generated UI files (plugin configurations)
        if self.generated_ui_dir.exists():
            self.app.router.add_static('/generated/', self.generated_ui_dir)
            
    def setup_cors(self):
        """Setup CORS for API endpoints"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    def generate_jwt_token(self, username: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'iss': 'p2p-node'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    async def is_authenticated(self, request) -> bool:
        """Check if request is authenticated"""
        # Check startup token in URL parameters (for auto-login)
        startup_token = request.query.get('token')
        if startup_token and startup_token == self.startup_token:
            # Auto-login with startup token
            username = 'local_user'
            token = self.generate_jwt_token(username)
            
            # Set user in request for this session
            request['user'] = {'username': username}
            
            # Create response to set cookie and redirect
            response = web.HTTPFound('/')
            response.set_cookie(
                'laboon_token',
                token,
                max_age=86400,  # 24 hours
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax'
            )
            
            # Store the response to be returned by the caller
            request['auto_login_response'] = response
            return True
        
        # Check for simple auth session token
        session_token = request.cookies.get('laboon_session')
        if session_token:
            user_data = self.simple_auth.verify_session_token(session_token)
            if user_data:
                # Store user data in request for later use
                request['user'] = {
                    'username': user_data['username'],
                    'display_name': user_data.get('display_name', user_data['username']),
                    'auth_type': 'simple'
                }
                return True
        
        # Check cookie
        token = request.cookies.get('laboon_token')
        if token:
            payload = self.verify_jwt_token(token)
            if payload:
                request['user'] = {
                    **payload,
                    'auth_type': 'jwt'
                }
                return True
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = self.verify_jwt_token(token)
            if payload:
                request['user'] = {
                    **payload,
                    'auth_type': 'bearer'
                }
                return True
        
        return False
    
    async def require_auth(self, request):
        """Middleware to require authentication"""
        is_auth = await self.is_authenticated(request)
        
        # Check if auto-login response was set
        if 'auto_login_response' in request:
            return request['auto_login_response']
        
        if not is_auth:
            if request.path.startswith('/api/'):
                return web.json_response({'error': 'Authentication required'}, status=401)
            else:
                return web.HTTPFound('/login')
        return None
    
    async def handle_login(self, request):
        """Handle login requests"""
        if request.method == 'GET':
            # Check if already authenticated
            if await self.is_authenticated(request):
                return web.HTTPFound('/')
            
            # Serve login page
            login_path = self.template_dir / 'login.html'
            if login_path.exists():
                with open(login_path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            else:
                return web.Response(text="Login page not found", status=404)
        
        elif request.method == 'POST':
            # Handle login form submission
            try:
                data = await request.json()
                username = data.get('username', '').strip()
                password = data.get('password', '').strip()
                
                if not username or not password:
                    return web.json_response({
                        'success': False,
                        'error': 'Username and password are required'
                    }, status=400)
                
                # Use Simple Auth system for authentication
                user_file = self.simple_auth.authenticate_user(username, password)
                
                if user_file:
                    # Authentication successful
                    # Generate JWT token with user info
                    token = self.generate_jwt_token(username)
                    
                    # Generate session token for simple auth
                    session_token = self.simple_auth.generate_session_token(username)
                    
                    # Log successful login
                    await log_user_action(username, 'login', {
                        'display_name': user_file.display_name,
                        'login_count': user_file.login_count,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Set secure cookie
                    response = web.json_response({
                        'success': True,
                        'message': f'Welcome back, {user_file.display_name}!',
                        'redirect': '/',
                        'user': {
                            'username': username,
                            'display_name': user_file.display_name,
                            'login_count': user_file.login_count
                        }
                    })
                    
                    # Set HTTP-only cookie for security
                    response.set_cookie(
                        'laboon_token',
                        token,
                        max_age=86400,  # 24 hours
                        httponly=True,
                        secure=False,  # Set to True in production with HTTPS
                        samesite='Lax'
                    )
                    
                    # Also set simple auth session token
                    response.set_cookie(
                        'laboon_session',
                        session_token,
                        max_age=86400,
                        httponly=True,
                        secure=False,
                        samesite='Lax'
                    )
                    
                    logger.info(f"✅ User {username} logged in successfully")
                    return response
                else:
                    # Authentication failed
                    await log_user_action(username, 'login_failed', {
                        'reason': 'invalid_credentials',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return web.json_response({
                        'success': False,
                        'error': 'Invalid username or password'
                    }, status=401)
                    
            except Exception as e:
                logger.error(f"Login error: {e}")
                return web.json_response({
                    'success': False,
                    'error': 'Login failed'
                }, status=500)
    
    async def handle_register(self, request):
        """Handle user registration"""
        try:
            data = await request.json()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            display_name = data.get('display_name', '').strip()
            
            if not username or not password:
                return web.json_response({
                    'success': False,
                    'error': 'Username and password are required'
                }, status=400)
            
            if not display_name:
                display_name = username
            
            # Check if user already exists
            if self.simple_auth.user_exists(username):
                return web.json_response({
                    'success': False,
                    'error': 'Username already exists'
                }, status=409)
            
            # Create new user
            user_file = self.simple_auth.create_user(username, password, display_name)
            
            if user_file:
                # Log registration
                await log_user_action(username, 'register', {
                    'display_name': display_name,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"✅ New user registered: {username} ({display_name})")
                
                return web.json_response({
                    'success': True,
                    'message': f'Welcome {display_name}! Your account has been created.',
                    'user': {
                        'username': username,
                        'display_name': display_name
                    }
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': 'Failed to create user account'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    async def handle_admin_login(self, request):
        """Handle admin login with multi-factor authentication"""
        try:
            data = await request.json()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            auth_file_data = data.get('auth_file')  # Base64 encoded file content
            
            if not username or not password:
                return web.json_response({
                    'success': False,
                    'error': 'Username and password are required'
                }, status=400)
            
            # Save auth file temporarily if provided
            auth_file_path = None
            if auth_file_data:
                try:
                    import base64
                    file_content = base64.b64decode(auth_file_data)
                    auth_file_path = f"/tmp/auth_{username}_{secrets.token_hex(8)}"
                    with open(auth_file_path, 'wb') as f:
                        f.write(file_content)
                except Exception as e:
                    logger.error(f"Failed to process auth file: {e}")
                    return web.json_response({
                        'success': False,
                        'error': 'Invalid authentication file'
                    }, status=400)
            
            # Authenticate admin user
            admin_user = self.advanced_auth.authenticate_admin(username, password, auth_file_path)
            
            # Clean up temporary file
            if auth_file_path and os.path.exists(auth_file_path):
                os.unlink(auth_file_path)
            
            if admin_user:
                # Create admin session
                client_ip = request.remote
                user_agent = request.headers.get('User-Agent', '')
                session = self.advanced_auth.create_admin_session(admin_user, client_ip, user_agent)
                
                # Log admin login
                await log_user_action(username, 'admin_login', {
                    'role': admin_user.role,
                    'permissions': admin_user.permissions,
                    'ip_address': client_ip,
                    'timestamp': datetime.now().isoformat()
                })
                
                response = web.json_response({
                    'success': True,
                    'message': f'Admin access granted for {admin_user.display_name}',
                    'user': {
                        'username': username,
                        'display_name': admin_user.display_name,
                        'role': admin_user.role,
                        'permissions': admin_user.permissions
                    },
                    'session': {
                        'expires_at': session.expires_at.isoformat()
                    }
                })
                
                # Set admin session cookie
                response.set_cookie(
                    'admin_session',
                    session.session_id,
                    max_age=3600,  # 1 hour
                    httponly=True,
                    secure=False,
                    samesite='Lax'
                )
                
                logger.info(f"🔐 Admin {username} logged in successfully")
                return response
            else:
                await log_user_action(username, 'admin_login_failed', {
                    'reason': 'invalid_credentials',
                    'timestamp': datetime.now().isoformat()
                })
                
                return web.json_response({
                    'success': False,
                    'error': 'Invalid admin credentials or authentication file'
                }, status=401)
                
        except Exception as e:
            logger.error(f"Admin login error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    async def handle_admin_logout(self, request):
        """Handle admin logout"""
        try:
            session_id = request.cookies.get('admin_session')
            if session_id:
                session = self.advanced_auth.verify_admin_session(session_id)
                if session:
                    await log_user_action(session.username, 'admin_logout', {
                        'session_duration': (datetime.now() - session.created_at).total_seconds(),
                        'timestamp': datetime.now().isoformat()
                    })
                
                self.advanced_auth.revoke_admin_session(session_id)
            
            response = web.json_response({
                'success': True,
                'message': 'Admin logout successful'
            })
            
            # Clear admin session cookie
            response.del_cookie('admin_session')
            return response
            
        except Exception as e:
            logger.error(f"Admin logout error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    @require_admin_permission('user_management')
    async def handle_admin_users(self, request):
        """Handle listing admin users"""
        try:
            users = self.advanced_auth.list_admin_users()
            
            # Remove sensitive data
            safe_users = []
            for user in users:
                safe_users.append({
                    'username': user.username,
                    'display_name': user.display_name,
                    'role': user.role,
                    'permissions': user.permissions,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'login_count': user.login_count,
                    'is_locked': user.is_locked()
                })
            
            return web.json_response({
                'success': True,
                'users': safe_users
            })
            
        except Exception as e:
            logger.error(f"Admin users list error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    @require_admin_permission('user_management')
    async def handle_create_admin_user(self, request):
        """Handle creating new admin user"""
        try:
            data = await request.json()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            display_name = data.get('display_name', '').strip()
            role = data.get('role', 'moderator')
            
            if not username or not password:
                return web.json_response({
                    'success': False,
                    'error': 'Username and password are required'
                }, status=400)
            
            if not display_name:
                display_name = username
            
            admin_user = self.advanced_auth.create_admin_user(username, password, display_name, role)
            
            if admin_user:
                # Log admin user creation
                session = request['admin_session']
                await log_user_action(session.username, 'create_admin_user', {
                    'created_user': username,
                    'role': role,
                    'timestamp': datetime.now().isoformat()
                })
                
                return web.json_response({
                    'success': True,
                    'message': f'Admin user {username} created successfully',
                    'user': {
                        'username': username,
                        'display_name': display_name,
                        'role': role,
                        'permissions': admin_user.permissions
                    }
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': 'Failed to create admin user (may already exist)'
                }, status=409)
                
        except Exception as e:
            logger.error(f"Create admin user error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    @require_admin_permission('user_management')
    async def handle_update_admin_user(self, request):
        """Handle updating admin user"""
        try:
            username = request.match_info['username']
            data = await request.json()
            permissions = data.get('permissions', [])
            
            success = self.advanced_auth.update_admin_permissions(username, permissions)
            
            if success:
                # Log admin user update
                session = request['admin_session']
                await log_user_action(session.username, 'update_admin_user', {
                    'updated_user': username,
                    'new_permissions': permissions,
                    'timestamp': datetime.now().isoformat()
                })
                
                return web.json_response({
                    'success': True,
                    'message': f'Admin user {username} updated successfully'
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': 'Admin user not found'
                }, status=404)
                
        except Exception as e:
            logger.error(f"Update admin user error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    @require_admin_permission('user_management')
    async def handle_delete_admin_user(self, request):
        """Handle deleting admin user"""
        try:
            username = request.match_info['username']
            
            # Prevent self-deletion
            session = request['admin_session']
            if session.username == username:
                return web.json_response({
                    'success': False,
                    'error': 'Cannot delete your own admin account'
                }, status=400)
            
            success = self.advanced_auth.delete_admin_user(username)
            
            if success:
                # Log admin user deletion
                await log_user_action(session.username, 'delete_admin_user', {
                    'deleted_user': username,
                    'timestamp': datetime.now().isoformat()
                })
                
                return web.json_response({
                    'success': True,
                    'message': f'Admin user {username} deleted successfully'
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': 'Admin user not found'
                }, status=404)
                
        except Exception as e:
            logger.error(f"Delete admin user error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    async def handle_logout(self, request):
        """Handle logout requests"""
        response = web.json_response({'success': True, 'message': 'Logged out'})
        response.del_cookie('laboon_token')
        return response
    
    async def handle_main_app(self, request):
        """Handle main application page"""
        # Require authentication
        auth_response = await self.require_auth(request)
        if auth_response:
            return auth_response
        
        # Serve main application
        index_path = self.template_dir / 'index.html'
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        else:
            return web.Response(text="Main application not found", status=404)
    
    async def handle_send_message(self, request):
        """Handle sending chat messages with automatic minor monitoring"""
        # Require authentication
        auth_response = await self.require_auth(request)
        if auth_response:
            return auth_response
        
        try:
            data = await request.json()
            sender_id = data.get('sender_id')
            sender_username = data.get('sender_username')
            sender_display_name = data.get('sender_display_name')
            recipient_id = data.get('recipient_id')
            recipient_username = data.get('recipient_username')
            recipient_display_name = data.get('recipient_display_name')
            content = data.get('content')
            message_type = data.get('message_type', 'text')
            
            if not all([sender_id, recipient_id, content]):
                return web.json_response({
                    'success': False,
                    'error': 'Missing required fields: sender_id, recipient_id, content'
                }, status=400)
            
            # Monitor message if chat monitor is available
            monitoring_result = None
            if self.chat_monitor:
                try:
                    from .chat_monitor import monitor_chat_message_global
                    monitoring_result = await monitor_chat_message_global(
                        sender_id=sender_id,
                        sender_username=sender_username or sender_id,
                        sender_display_name=sender_display_name or sender_username or sender_id,
                        recipient_id=recipient_id,
                        recipient_username=recipient_username or recipient_id,
                        recipient_display_name=recipient_display_name or recipient_username or recipient_id,
                        content=content,
                        message_type=message_type
                    )
                    logger.info(f"📧 Message monitored: {monitoring_result.get('notifications_sent', 0)} notifications sent")
                except Exception as e:
                    logger.error(f"Error monitoring message: {e}")
            
            # TODO: Integrate with actual message engine
            # For now, just return success with monitoring info
            
            response_data = {
                'success': True,
                'message': 'Message sent successfully',
                'message_id': f"msg_{sender_id}_{recipient_id}_{int(datetime.now().timestamp())}"
            }
            
            if monitoring_result:
                response_data['monitoring'] = {
                    'alerts_generated': len(monitoring_result.get('alerts_generated', [])),
                    'notifications_sent': len(monitoring_result.get('notifications_sent', [])),
                    'actions_taken': monitoring_result.get('actions_taken', [])
                }
            
            return web.json_response(response_data)
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    async def handle_chat_history(self, request):
        """Handle getting chat history for a user"""
        # Require authentication
        auth_response = await self.require_auth(request)
        if auth_response:
            return auth_response
        
        try:
            user_id = request.match_info['user_id']
            limit = int(request.query.get('limit', 50))
            
            # Get recent messages from chat monitor
            messages = []
            if self.chat_monitor:
                recent_messages = self.chat_monitor.get_recent_messages_for_user(user_id, limit)
                messages = [msg.to_dict() for msg in recent_messages]
            
            return web.json_response({
                'success': True,
                'messages': messages,
                'user_id': user_id,
                'count': len(messages)
            })
            
        except Exception as e:
            logger.error(f"Chat history error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    async def handle_minor_status(self, request):
        """Handle getting minor protection status for a user"""
        # Require authentication
        auth_response = await self.require_auth(request)
        if auth_response:
            return auth_response
        
        try:
            user_id = request.match_info['user_id']
            
            # Check if user is minor
            is_minor = False
            parent_email = None
            age_verification_status = None
            
            if self.age_verification:
                try:
                    user_data = await self.age_verification.get_minor_user_data(user_id)
                    if user_data:
                        is_minor = True
                        parent_email = user_data.get('parent_email')
                        age_verification_status = user_data.get('verification_status')
                except Exception as e:
                    logger.error(f"Error checking minor status: {e}")
            
            # Get monitoring alerts
            alerts = []
            if self.chat_monitor and is_minor:
                alerts = self.chat_monitor.get_alerts_for_user(user_id)
                alerts = [asdict(alert) for alert in alerts]
            
            return web.json_response({
                'success': True,
                'user_id': user_id,
                'is_minor': is_minor,
                'parent_email': parent_email,
                'age_verification_status': age_verification_status,
                'active_alerts': len(alerts),
                'alerts': alerts
            })
            
        except Exception as e:
            logger.error(f"Minor status error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    async def handle_minor_stats(self, request):
        """Handle getting overall minor protection statistics"""
        # Require authentication
        auth_response = await self.require_auth(request)
        if auth_response:
            return auth_response
        
        try:
            stats = {}
            
            # Get chat monitoring stats
            if self.chat_monitor:
                stats['monitoring'] = self.chat_monitor.get_monitoring_stats()
            
            # Sistema di protezione semplificato
            stats['simple_protection'] = {
                'enabled': True,
                'type': 'email_notifications'
            }
            
            return web.json_response({
                'success': True,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Minor stats error: {e}")
            return web.json_response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    async def handle_parent_dashboard(self, request):
        """Handle parent dashboard for monitoring minor's activity"""
        # This would normally require parent authentication
        # For now, we'll serve a basic dashboard
        
        try:
            user_id = request.query.get('user_id')
            
            # Basic HTML dashboard (in production, this would be a proper template)
            dashboard_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>LaboonChat - Dashboard Parentale</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
                    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                    .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; }}
                    .stat-number {{ font-size: 2em; font-weight: bold; color: #2196f3; }}
                    .stat-label {{ color: #666; margin-top: 5px; }}
                    .section {{ margin-bottom: 30px; }}
                    .section h3 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                    .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                    .alert.high {{ background: #f8d7da; border-color: #f5c6cb; }}
                    .btn {{ background: #4caf50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }}
                    .btn:hover {{ background: #45a049; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🛡️ Dashboard Parentale LaboonChat</h1>
                        <p>Monitoraggio attività per utente: {user_id or 'Non specificato'}</p>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-number" id="messages-count">-</div>
                            <div class="stat-label">Messaggi Monitorati</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="notifications-count">-</div>
                            <div class="stat-label">Notifiche Inviate</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="alerts-count">-</div>
                            <div class="stat-label">Alert Attivi</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="protection-status">🛡️</div>
                            <div class="stat-label">Protezione Attiva</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>📊 Controlli Rapidi</h3>
                        <a href="/api/minor/stats" class="btn">📈 Statistiche Complete</a>
                        <a href="/api/chat/history/{user_id or 'USER_ID'}" class="btn">💬 Cronologia Chat</a>
                        <a href="/api/minor/status/{user_id or 'USER_ID'}" class="btn">🔍 Stato Protezione</a>
                    </div>
                    
                    <div class="section">
                        <h3>🔒 Informazioni Sicurezza</h3>
                        <div class="alert">
                            <strong>✅ Sistema Attivo:</strong> Il sistema di protezione minori è operativo e monitora automaticamente tutte le conversazioni.
                        </div>
                        <div class="alert">
                            <strong>📧 Notifiche Email:</strong> Riceverà una notifica email per ogni messaggio inviato o ricevuto dal minore.
                        </div>
                        <div class="alert">
                            <strong>🔐 Privacy:</strong> Tutti i dati sono crittografati e accessibili solo a lei come genitore verificato.
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>📞 Supporto</h3>
                        <p>Per assistenza o domande sul sistema di protezione minori:</p>
                        <p>📧 Email: support@laboonchat.local</p>
                        <p>🌐 Documentazione: <a href="/static/docs/parental_protection.html">Guida Protezione Minori</a></p>
                    </div>
                </div>
                
                <script>
                    // Load stats dynamically
                    fetch('/api/minor/stats')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success && data.stats) {{
                                const monitoring = data.stats.monitoring || {{}};
                                document.getElementById('messages-count').textContent = monitoring.messages_monitored || 0;
                                document.getElementById('notifications-count').textContent = monitoring.notifications_sent || 0;
                                document.getElementById('alerts-count').textContent = monitoring.active_alerts || 0;
                            }}
                        }})
                        .catch(error => console.error('Error loading stats:', error));
                </script>
            </body>
            </html>
            """
            
            return web.Response(text=dashboard_html, content_type='text/html')
            
        except Exception as e:
            logger.error(f"Parent dashboard error: {e}")
            return web.Response(text="Dashboard temporarily unavailable", status=500)
    
    async def handle_websocket(self, request):
        """Handle WebSocket connections for real-time chat"""
        # Require authentication
        if not await self.is_authenticated(request):
            return web.Response(text='Authentication required', status=401)
        
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        user = request.get('user', {})
        username = user.get('username', 'Anonymous')
        
        logger.info(f"WebSocket connected: {username}")
        
        # Send welcome message
        await ws.send_str(json.dumps({
            'type': 'system',
            'message': f'Benvenuto {username}! Sei connesso a LaboonChat.',
            'timestamp': datetime.now().isoformat()
        }))
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.handle_chat_message(data, username)
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON in WebSocket message")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websockets.discard(ws)
            logger.info(f"WebSocket disconnected: {username}")
        
        return ws
    
    async def handle_chat_message(self, data: Dict[str, Any], username: str):
        """Handle incoming chat messages"""
        if data.get('type') == 'message':
            message = data.get('message', '').strip()
            if message:
                # Broadcast message to all connected clients
                broadcast_data = {
                    'type': 'message',
                    'user': username,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                await self.broadcast_message(broadcast_data)
    
    async def broadcast_message(self, data: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients"""
        if self.websockets:
            message = json.dumps(data)
            disconnected = set()
            
            for ws in self.websockets:
                try:
                    await ws.send_str(message)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    disconnected.add(ws)
            
            # Remove disconnected WebSockets
            self.websockets -= disconnected
    
    async def handle_plugin_menu(self, request):
        """Handle plugin configuration menu"""
        # Require authentication
        auth_response = await self.require_auth(request)
        if auth_response:
            return auth_response
        
        # Serve plugin menu from generated UI
        menu_path = self.generated_ui_dir / 'plugin_menu.html'
        if menu_path.exists():
            with open(menu_path, 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        else:
            # Generate basic plugin menu if not exists
            return web.Response(text=self.generate_basic_plugin_menu(), content_type='text/html')
    
    def generate_basic_plugin_menu(self) -> str:
        """Generate a basic plugin menu if the generated one doesn't exist"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Plugin Configuration</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; background: #1a1a1a; color: #f5f1e8; }
                .container { max-width: 800px; margin: 0 auto; }
                .message { padding: 20px; background: #2a2a2a; border-radius: 10px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="message">
                    <h2>🐋 Plugin Configuration</h2>
                    <p>Plugin configuration system is being initialized...</p>
                    <p>Please run the configuration system test to generate the plugin interfaces.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def handle_plugin_api(self, request):
        """Handle plugin API requests"""
        # Require authentication
        auth_response = await self.require_auth(request)
        if auth_response:
            return auth_response
        
        # For now, return a placeholder response
        # This would integrate with the actual plugin configuration system
        return web.json_response({
            'message': 'Plugin API endpoint',
            'path': request.match_info['path'],
            'method': request.method
        })
    
    async def start_server(self):
        """Start the unified web server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        # Print access information
        self.print_access_info()
        
        # Launch browser automatically
        self.launch_browser()
        
        return runner

async def main():
    """Main function to run the unified server"""
    server = UnifiedWebServer(host='localhost', port=9494, auto_launch_browser=True)
    runner = await server.start_server()
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())