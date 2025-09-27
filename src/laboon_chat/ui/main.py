#!/usr/bin/env python3
"""
🌐 P2P Messaging Web Interface Launcher
=======================================
Main entry point for the P2P messaging web interface.
Launches the web server with the creamy dark theme.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.web_server import WebServer
from ui.chat_interface import ChatInterface

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='🌐 %(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main function to start the P2P messaging web interface
    """
    logger.info("🌐 Starting P2P Messaging Web Interface...")
    
    try:
        # Create chat interface (for demo data and UI management)
        chat_interface = ChatInterface()
        
        # Create and configure web server
        web_server = WebServer(
            host='localhost',
            port=8080,
            message_engine=None  # Will be integrated later
        )
        
        # Start the server
        logger.info("🌐 Starting web server on http://localhost:8080")
        await web_server.start()
        
    except KeyboardInterrupt:
        logger.info("🌐 Shutting down P2P Messaging...")
    except Exception as e:
        logger.error(f"🌐 Error starting P2P Messaging: {e}")
        raise


def run():
    """
    Convenience function to run the web interface
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🌐 P2P Messaging stopped by user")
    except Exception as e:
        logger.error(f"🌐 Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # Quick start options
    import argparse
    
    parser = argparse.ArgumentParser(description='🌐 P2P Messaging Web Interface')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🌐 Debug mode enabled")
    
    logger.info(f"🌐 P2P Messaging Web Interface starting...")
    logger.info(f"🌐 Host: {args.host}")
    logger.info(f"🌐 Port: {args.port}")
    logger.info(f"🌐 URL: http://{args.host}:{args.port}")
    
    # Override default settings if provided
    if args.host != 'localhost' or args.port != 8080:
        async def main_with_args():
            chat_interface = ChatInterface()
            web_server = WebServer(
                host=args.host,
                port=args.port,
                message_engine=None
            )
            await web_server.start()
        
        try:
            asyncio.run(main_with_args())
        except KeyboardInterrupt:
            logger.info("🌐 P2P Messaging stopped by user")
        except Exception as e:
            logger.error(f"🌐 Fatal error: {e}")
            sys.exit(1)
    else:
        run()