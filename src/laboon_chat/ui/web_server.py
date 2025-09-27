"""
P2P Messaging Web Server
========================

Async HTTP server for P2P messaging web interface.
Serves the dark creamy theme UI with security integration.

🌐 Decentralized connections with individual responsibility 🌊
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response, WebSocketResponse
import aiohttp_cors
import uuid
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebServer:
    """
    🌐 P2P Messaging Web Server
    ===========================
    Asynchronous web server for P2P messaging web interface.
    Handles HTTP routes, WebSocket connections, and static file serving.
    """
    
    def __init__(self, host='localhost', port=8080, message_engine=None):
        self.host = host
        self.port = port
        self.message_engine = message_engine
        self.app = None
        self.websockets = set()
        
        # Setup Jinja2 templates
        self.setup_templates()
        
        # Demo data (will be replaced with real MessageEngine integration)
        self.demo_contacts = [
            {
                'id': 'alice',
                'name': 'Alice',
                'avatar': '👩‍💻',
                'status': 'online',
                'last_seen': '2 min ago',
                'key_type': 'solid',
                'trust_level': 95
            },
            {
                'id': 'bob',
                'name': 'Bob',
                'avatar': '👨‍🔬',
                'status': 'away',
                'last_seen': '1 hour ago',
                'key_type': 'liquid',
                'trust_level': 78
            }
        ]
        
        self.demo_messages = {
            'alice': [
                {
                    'id': '1',
                    'sender': 'alice',
                    'text': 'Hey! How are you doing?',
                    'timestamp': '2024-01-27T10:30:00Z',
                    'encrypted': True,
                    'verified': True
                },
                {
                    'id': '2',
                    'sender': 'me',
                    'text': 'Great! Working on the new P2P messaging interface 🌐',
                    'timestamp': '2024-01-27T10:31:00Z',
                    'encrypted': True,
                    'verified': True
                }
            ],
            'bob': [
                {
                    'id': '3',
                    'sender': 'bob',
                    'text': 'The liquid key system is working perfectly!',
                    'timestamp': '2024-01-27T09:15:00Z',
                    'encrypted': True,
                    'verified': True
                }
            ]
        }
    
    def setup_templates(self):
        """Setup Jinja2 template environment"""
        current_dir = Path(__file__).parent
        template_dir = current_dir / 'templates'
        
        if not template_dir.exists():
            template_dir.mkdir(exist_ok=True)
            
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
        # Initialize app and other components
        self.app = web.Application()
        self.active_connections = {}
        self.secret_key = 'laboon-secret-key-' + str(uuid.uuid4())
        
        # Setup routes
        self._setup_routes()
        self._setup_cors()
        
    def _setup_routes(self):
        """Setup HTTP routes and WebSocket endpoints"""
        # Static files
        self.app.router.add_get('/', self._serve_disclaimer)
        self.app.router.add_get('/disclaimer', self._serve_disclaimer)
        self.app.router.add_get('/login', self._serve_login)
        self.app.router.add_get('/app', self._serve_app)
        self.app.router.add_static('/static/', path=Path(__file__).parent / 'static')
        
        # API endpoints
        self.app.router.add_post('/api/auth', self._handle_auth)
        self.app.router.add_get('/api/contacts', self._handle_get_contacts)
        self.app.router.add_post('/api/send-message', self._handle_send_message)
        self.app.router.add_get('/api/messages/{contact_id}', self._handle_get_messages)
        
        # WebSocket for real-time
        self.app.router.add_get('/ws', self._handle_websocket)
        
    def _setup_cors(self):
        """Setup CORS for local development"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "http://localhost:8847": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def _serve_disclaimer(self, request: Request) -> Response:
        """Serve disclaimer page with responsibility acceptance"""
        try:
            template = self.jinja_env.get_template('disclaimer.html')
            html = template.render()
            return Response(text=html, content_type='text/html')
        except Exception as e:
            # Fallback se il template non esiste
            return Response(text="Disclaimer template not found", status=500)
    
    async def _serve_login(self, request: Request) -> Response:
        """Serve login page after disclaimer acceptance"""
        try:
            template = self.jinja_env.get_template('login.html')
            html = template.render()
            return Response(text=html, content_type='text/html')
        except Exception as e:
            # Fallback se il template non esiste
            return Response(text="Login template not found", status=500)
    
    async def _serve_index(self, request: Request) -> Response:
        """Serve landing page with launcher integration (deprecated - now redirects to disclaimer)"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>P2P Messaging - Decentralized Connections</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    color: #f5f5dc;
                    margin: 0;
                    padding: 40px;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    text-align: center;
                    max-width: 600px;
                }
                h1 {
                    font-size: 3em;
                    margin-bottom: 20px;
                    background: linear-gradient(45deg, #d4af37, #f5f5dc);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .whale { font-size: 4em; margin: 20px 0; }
                .launch-btn {
                    background: linear-gradient(45deg, #d4af37, #b8860b);
                    color: #1a1a1a;
                    border: none;
                    padding: 15px 30px;
                    font-size: 1.2em;
                    border-radius: 25px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 30px;
                }
                .launch-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(212, 175, 55, 0.3);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="whale">🌐</div>
                <h1>P2P Messaging</h1>
                <p>Decentralized connections with individual responsibility</p>
                <a href="/app" class="launch-btn">Launch P2P Messaging</a>
            </div>
        </body>
        </html>
        """
        return Response(text=html, content_type='text/html')
    
    async def _serve_app(self, request: Request) -> Response:
        """Serve main chat application"""
        # Generate session token
        token = jwt.encode({
            'session_id': str(uuid.uuid4()),
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }, self.secret_key, algorithm='HS256')
        
        # Load the main app HTML (will be created next)
        app_html = await self._load_app_html(token)
        return Response(text=app_html, content_type='text/html')
    
    async def _load_app_html(self, token: str) -> str:
        """Load main application HTML with dark creamy theme"""
        # This will load our main chat interface
        # For now, return a placeholder that will be replaced with full UI
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>P2P Messaging</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="/static/app.css">
        </head>
        <body>
            <div id="app">
                <div class="loading">
                    <div class="whale">🌐</div>
                    <p>Loading P2P Messaging...</p>
                </div>
            </div>
            <script>
                window.P2P_TOKEN = '{token}';
                window.P2P_WS_URL = 'ws://localhost:8847/ws';
            </script>
            <script src="/static/app.js"></script>
        </body>
        </html>
        """
    
    # API Handlers
    async def _handle_auth(self, request: Request) -> Response:
        """Handle authentication"""
        return web.json_response({'status': 'authenticated', 'user_id': 'demo_user'})
    
    async def _handle_get_contacts(self, request: Request) -> Response:
        """Get contact list with security indicators"""
        # Demo contacts with security levels
        contacts = [
            {
                'id': 'alice',
                'name': 'Alice',
                'avatar': '👩‍💻',
                'key_type': 'solid',
                'trust_level': 95,
                'last_seen': '2 min ago',
                'status': 'online'
            },
            {
                'id': 'bob',
                'name': 'Bob',
                'avatar': '👨‍🔬',
                'key_type': 'liquid',
                'trust_level': 78,
                'last_seen': '1 hour ago',
                'status': 'away'
            }
        ]
        return web.json_response({'contacts': contacts})
    
    async def _handle_send_message(self, request: Request) -> Response:
        """Send message through MessageEngine"""
        data = await request.json()
        # TODO: Integrate with actual MessageEngine
        message_id = str(uuid.uuid4())
        
        # Broadcast to WebSocket connections
        await self._broadcast_message({
            'type': 'new_message',
            'message': {
                'id': message_id,
                'contact_id': data['contact_id'],
                'text': data['text'],
                'timestamp': datetime.utcnow().isoformat(),
                'sender': 'me'
            }
        })
        
        return web.json_response({'message_id': message_id, 'status': 'sent'})
    
    async def _handle_get_messages(self, request: Request) -> Response:
        """Get message history for contact"""
        contact_id = request.match_info['contact_id']
        # Demo messages
        messages = [
            {
                'id': '1',
                'text': 'Hey! How are you?',
                'sender': contact_id,
                'timestamp': '2024-01-27T10:00:00Z'
            },
            {
                'id': '2', 
                'text': 'Great! Just testing P2P messaging 🌐',
                'sender': 'me',
                'timestamp': '2024-01-27T10:01:00Z'
            }
        ]
        return web.json_response({'messages': messages})
    
    async def _handle_websocket(self, request: Request) -> WebSocketResponse:
        """Handle WebSocket connections for real-time messaging"""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = ws
        
        logger.info(f"WebSocket connected: {connection_id}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_ws_message(connection_id, data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.active_connections.pop(connection_id, None)
            logger.info(f"WebSocket disconnected: {connection_id}")
        
        return ws
    
    async def _handle_ws_message(self, connection_id: str, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        msg_type = data.get('type')
        
        if msg_type == 'ping':
            await self.active_connections[connection_id].send_str(
                json.dumps({'type': 'pong'})
            )
        elif msg_type == 'typing':
            # Broadcast typing indicator
            await self._broadcast_message(data, exclude=connection_id)
    
    async def _broadcast_message(self, message: Dict[str, Any], exclude: Optional[str] = None):
        """Broadcast message to all connected WebSocket clients"""
        if not self.active_connections:
            return
            
        message_str = json.dumps(message)
        
        for conn_id, ws in list(self.active_connections.items()):
            if exclude and conn_id == exclude:
                continue
                
            try:
                await ws.send_str(message_str)
            except Exception as e:
                logger.error(f"Failed to send to {conn_id}: {e}")
                self.active_connections.pop(conn_id, None)
    
    def set_message_engine(self, engine):
        """Inject MessageEngine dependency"""
        self.message_engine = engine
    
    async def start(self):
        """Start the web server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"🌐 P2P Messaging Web Server started at http://{self.host}:{self.port}")
        return runner
    
    async def stop(self, runner):
        """Stop the web server"""
        await runner.cleanup()
        logger.info("🌐 P2P Messaging Web Server stopped")


async def main():
    """Main function to run the web server"""
    import signal
    
    server = WebServer()
    runner = None
    
    try:
        runner = await server.start()
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🌐 Shutting down P2P Messaging Web Server...")
    except Exception as e:
        logger.error(f"🌐 Server error: {e}")
    finally:
        if runner:
            await server.stop(runner)


if __name__ == "__main__":
    asyncio.run(main())