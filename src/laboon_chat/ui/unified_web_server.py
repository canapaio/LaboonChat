"""
🌐 P2P Messaging Unified Web Server
===================================

Server web unificato che integra:
- Interfaccia chat principale
- Sistema di configurazione plugin
- Autenticazione decentralizzata
- Routing interno per navigazione seamless

🌐 "Un solo accesso, infinite possibilità decentralizzate" 🌐
"""

import asyncio
import logging
import json
import jwt
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response, WebSocketResponse
import aiohttp_cors
from jinja2 import Environment, FileSystemLoader

# Import sistema configurazione esistente
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

try:
    from plugin_config_system import PluginConfigManager
    from config_ui_generator import ConfigUIGenerator
    from config_integration import ConfigIntegration
except ImportError:
    # Fallback per sviluppo
    PluginConfigManager = None
    ConfigUIGenerator = None
    ConfigIntegration = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedWebServer:
    """
    🌐 Server Web Unificato P2P Messaging
    =====================================
    
    Combina chat e configurazioni in un'unica interfaccia
    con autenticazione decentralizzata e routing interno.
    """
    
    def __init__(self, host='localhost', port=8080, message_engine=None):
        self.host = host
        self.port = port
        self.message_engine = message_engine
        self.app = None
        self.websockets = set()
        
        # JWT Configuration
        self.jwt_secret = secrets.token_urlsafe(32)
        self.jwt_algorithm = 'HS256'
        self.token_expiry = timedelta(hours=24)
        
        # Setup templates
        self.setup_templates()
        
        # Setup configurazione plugin
        self.setup_plugin_config()
        
        # Demo data (sarà sostituito con integrazione reale)
        self.demo_contacts = [
            {'id': 'alice', 'name': 'Alice', 'status': 'online', 'last_seen': 'now'},
            {'id': 'bob', 'name': 'Bob', 'status': 'away', 'last_seen': '5 min ago'},
            {'id': 'charlie', 'name': 'Charlie', 'status': 'offline', 'last_seen': '2 hours ago'}
        ]
    
    def setup_templates(self):
        """Setup Jinja2 templates"""
        template_dir = Path(__file__).parent / 'templates'
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    def setup_plugin_config(self):
        """Setup sistema configurazione plugin"""
        try:
            if PluginConfigManager:
                self.config_manager = PluginConfigManager()
                self.ui_generator = ConfigUIGenerator(self.config_manager)
                self.config_integration = ConfigIntegration(self.config_manager, self.ui_generator)
                logger.info("✅ Sistema configurazione plugin caricato")
            else:
                logger.warning("⚠️ Sistema configurazione plugin non disponibile")
                self.config_manager = None
        except Exception as e:
            logger.error(f"❌ Errore caricamento configurazione: {e}")
            self.config_manager = None
    
    def generate_token(self, user_id: str = "default_user") -> str:
        """Genera JWT token per autenticazione"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow(),
            'iss': 'p2p-node'
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token scaduto")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token non valido")
            return None
    
    async def auth_middleware(self, request: Request, handler):
        """Middleware per autenticazione"""
        # Percorsi pubblici che non richiedono autenticazione
        public_paths = ['/login', '/static/', '/favicon.ico']
        
        if any(request.path.startswith(path) for path in public_paths):
            return await handler(request)
        
        # Verifica token
        token = request.headers.get('Authorization')
        if not token:
            token = request.cookies.get('laboon_token')
        
        if token and token.startswith('Bearer '):
            token = token[7:]
        
        if not token:
            return web.Response(status=401, text='Token richiesto')
        
        payload = self.verify_token(token)
        if not payload:
            return web.Response(status=401, text='Token non valido')
        
        # Aggiungi user info alla request
        request['user'] = payload
        return await handler(request)
    
    async def login_handler(self, request: Request) -> Response:
        """Handler per login"""
        if request.method == 'GET':
            # Mostra pagina di login
            template = self.jinja_env.get_template('login.html')
            html = template.render()
            return web.Response(text=html, content_type='text/html')
        
        elif request.method == 'POST':
            # Processa login (per ora accetta qualsiasi credenziale)
            data = await request.json()
            username = data.get('username', 'user')
            
            # Genera token
            token = self.generate_token(username)
            
            # Imposta cookie
            response = web.json_response({
                'success': True,
                'token': token,
                'redirect': '/'
            })
            response.set_cookie(
                'laboon_token', 
                token, 
                max_age=int(self.token_expiry.total_seconds()),
                httponly=True,
                secure=False,  # True in produzione con HTTPS
                samesite='Lax'
            )
            
            return response
    
    async def index_handler(self, request: Request) -> Response:
        """Handler per pagina principale unificata"""
        token = self.generate_token()
        
        template = self.jinja_env.get_template('unified_index.html')
        html = template.render(
            token=token,
            ws_url=f'ws://{self.host}:{self.port}/ws',
            api_base=f'http://{self.host}:{self.port}/api'
        )
        return web.Response(text=html, content_type='text/html')
    
    async def config_handler(self, request: Request) -> Response:
        """Handler per configurazioni plugin integrate"""
        if not self.config_manager:
            return web.json_response({
                'error': 'Sistema configurazione non disponibile'
            }, status=503)
        
        plugin_id = request.match_info.get('plugin_id')
        
        if not plugin_id:
            # Lista plugin disponibili
            plugins = list(self.config_manager.schemas.keys())
            return web.json_response({'plugins': plugins})
        
        # Configurazione specifica plugin
        try:
            config = self.config_manager.load_plugin_config(plugin_id)
            schema = self.config_manager.get_plugin_schema(plugin_id)
            
            return web.json_response({
                'plugin_id': plugin_id,
                'config': config,
                'schema': schema.to_json_schema() if schema else None
            })
        except Exception as e:
            return web.json_response({
                'error': f'Errore caricamento configurazione: {str(e)}'
            }, status=500)
    
    async def save_config_handler(self, request: Request) -> Response:
        """Handler per salvare configurazioni plugin"""
        if not self.config_manager:
            return web.json_response({
                'error': 'Sistema configurazione non disponibile'
            }, status=503)
        
        plugin_id = request.match_info.get('plugin_id')
        data = await request.json()
        
        try:
            # Valida e salva configurazione
            is_valid = self.config_manager.validate_plugin_config(plugin_id, data)
            if is_valid:
                self.config_manager.save_plugin_config(plugin_id, data)
                return web.json_response({'success': True})
            else:
                return web.json_response({
                    'error': 'Configurazione non valida'
                }, status=400)
        except Exception as e:
            return web.json_response({
                'error': f'Errore salvataggio: {str(e)}'
            }, status=500)
    
    async def contacts_handler(self, request: Request) -> Response:
        """Handler per lista contatti"""
        return web.json_response(self.demo_contacts)
    
    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """Handler WebSocket per messaggi real-time"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        logger.info(f"🔌 WebSocket connesso. Totale: {len(self.websockets)}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_websocket_message(ws, data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            logger.error(f"Errore WebSocket: {e}")
        finally:
            self.websockets.discard(ws)
            logger.info(f"🔌 WebSocket disconnesso. Totale: {len(self.websockets)}")
        
        return ws
    
    async def handle_websocket_message(self, ws: WebSocketResponse, data: Dict[str, Any]):
        """Gestisce messaggi WebSocket"""
        message_type = data.get('type')
        
        if message_type == 'send_message':
            # Simula invio messaggio
            response = {
                'type': 'message_sent',
                'message': {
                    'id': f"msg_{datetime.now().timestamp()}",
                    'from': 'me',
                    'to': data.get('to'),
                    'content': data.get('content'),
                    'timestamp': datetime.now().isoformat()
                }
            }
            await ws.send_str(json.dumps(response))
    
    def create_app(self) -> web.Application:
        """Crea applicazione web unificata"""
        app = web.Application(middlewares=[self.auth_middleware])
        
        # Setup CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Routes pubbliche
        app.router.add_route('*', '/login', self.login_handler)
        
        # Routes autenticate
        app.router.add_get('/', self.index_handler)
        app.router.add_get('/ws', self.websocket_handler)
        
        # API Routes
        app.router.add_get('/api/contacts', self.contacts_handler)
        app.router.add_get('/api/config', self.config_handler)
        app.router.add_get('/api/config/{plugin_id}', self.config_handler)
        app.router.add_post('/api/config/{plugin_id}', self.save_config_handler)
        
        # Static files
        static_dir = Path(__file__).parent / 'static'
        app.router.add_static('/static/', static_dir)
        
        # Aggiungi CORS a tutte le routes
        for route in list(app.router.routes()):
            cors.add(route)
        
        return app
    
    async def start(self):
        """Avvia server unificato"""
        self.app = self.create_app()
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"🌐 P2P Messaging Unified Server avviato su http://{self.host}:{self.port}")
        logger.info(f"🔐 Login: http://{self.host}:{self.port}/login")
        logger.info(f"⚙️ Configurazioni integrate nell'interfaccia principale")
        
        return runner
    
    async def stop(self, runner):
        """Ferma server"""
        await runner.cleanup()
        logger.info("🐋 Server fermato")

# Funzione di utilità per avvio rapido
async def start_unified_server(host='localhost', port=8080):
    """Avvia server unificato P2P Messaging"""
    server = UnifiedWebServer(host, port)
    runner = await server.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🌐 Arresto server...")
        await server.stop(runner)

if __name__ == '__main__':
    asyncio.run(start_unified_server())