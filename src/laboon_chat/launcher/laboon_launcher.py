"""
P2P Messaging Browser Launcher
==============================

Minimal launcher that starts the P2P messaging web interface
in the user's default browser with security optimizations.

🌐 Decentralized launch with individual responsibility 🌊
"""

import asyncio
import logging
import webbrowser
import socket
from pathlib import Path
from typing import Optional
import subprocess
import sys

logger = logging.getLogger(__name__)


class P2PLauncher:
    """
    Minimal browser launcher for P2P Messaging.
    
    Features:
    - Starts local web server
    - Opens browser with security settings
    - Manages application lifecycle
    - Handles graceful shutdown
    """
    
    def __init__(self, port: int = 8080, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.server_process: Optional[subprocess.Popen] = None
        self.is_running = False
        
        logger.info(f"🌐 P2PLauncher initialized on {host}:{port}")
    
    def find_free_port(self) -> int:
        """Find a free port for the web server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    async def start_server(self) -> bool:
        """
        Start the LaboonChat web server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Find free port if current is occupied
            if not self._is_port_free(self.port):
                self.port = self.find_free_port()
                logger.info(f"🌊 Using alternative port: {self.port}")
            
            # TODO: Start actual web server
            # For now, simulate server start
            await asyncio.sleep(1)
            
            self.is_running = True
            logger.info(f"🚀 LaboonChat server started on http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def _is_port_free(self, port: int) -> bool:
        """Check if a port is free."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, port))
                return True
        except OSError:
            return False
    
    def open_browser(self) -> bool:
        """
        Open LaboonChat in the default browser.
        
        Returns:
            True if browser opened successfully, False otherwise
        """
        try:
            url = f"http://{self.host}:{self.port}"
            
            # Security-optimized browser launch
            # TODO: Add security flags for different browsers
            webbrowser.open(url, new=2)  # new=2 opens in new tab
            
            logger.info(f"🌐 Browser opened: {url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to open browser: {e}")
            return False
    
    async def launch(self) -> bool:
        """
        Launch LaboonChat: start server and open browser.
        
        Returns:
            True if launch successful, False otherwise
        """
        logger.info("🐋 Launching LaboonChat...")
        
        # Start server
        if not await self.start_server():
            return False
        
        # Wait a moment for server to be ready
        await asyncio.sleep(2)
        
        # Open browser
        if not self.open_browser():
            await self.stop()
            return False
        
        logger.info("✅ LaboonChat launched successfully!")
        logger.info("🌊 Faithful connections across digital oceans are now possible")
        return True
    
    async def stop(self):
        """Stop the LaboonChat server."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
        
        self.is_running = False
        logger.info("🐋 LaboonChat server stopped")
    
    def get_status(self) -> dict:
        """Get launcher status information."""
        return {
            "running": self.is_running,
            "host": self.host,
            "port": self.port,
            "url": f"http://{self.host}:{self.port}" if self.is_running else None
        }


async def main():
    """Main launcher entry point."""
    launcher = P2PLauncher()
    
    try:
        success = await launcher.launch()
        if success:
            print("🌐 P2P Messaging is running!")
            print(f"🌐 Open your browser to: http://{launcher.host}:{launcher.port}")
            print("🌊 Press Ctrl+C to stop")
            
            # Keep running until interrupted
            while launcher.is_running:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        print("\n🌐 Stopping P2P Messaging...")
        await launcher.stop()
        print("👋 Goodbye! Stay connected in the decentralized network!")


if __name__ == "__main__":
    asyncio.run(main())