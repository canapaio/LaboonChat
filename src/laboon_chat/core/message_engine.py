"""
P2P Message Engine
=================

Core message processing engine for decentralized P2P messaging.
Handles message routing, encryption, and delivery across the P2P network.

This engine works tirelessly to connect peers across digital networks
with individual responsibility and no central authority.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a message in the LaboonChat network."""
    id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: datetime
    message_type: str = "text"
    encrypted: bool = True
    signature: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


class MessageEngine:
    """
    Core message processing engine for LaboonChat.
    
    Handles:
    - Message creation and validation
    - Message routing through P2P network
    - Message encryption/decryption
    - Message delivery confirmation
    - Message history management
    """
    
    def __init__(self):
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_messages: Dict[str, Message] = {}
        self.message_history: List[Message] = []
        self.is_running = False
        
        logger.info("🐋 LaboonChat MessageEngine initialized")
    
    async def start(self):
        """Start the message engine."""
        self.is_running = True
        logger.info("🌊 MessageEngine started - Ready to connect across digital oceans")
    
    async def stop(self):
        """Stop the message engine."""
        self.is_running = False
        logger.info("🐋 MessageEngine stopped")
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler for a specific message type."""
        self.message_handlers[message_type] = handler
        logger.debug(f"📝 Registered handler for message type: {message_type}")
    
    async def send_message(self, recipient_id: str, content: str, 
                          message_type: str = "text") -> str:
        """
        Send a message to a recipient.
        
        Args:
            recipient_id: ID of the message recipient
            content: Message content
            message_type: Type of message (text, file, etc.)
            
        Returns:
            Message ID for tracking
        """
        message = Message(
            id=str(uuid.uuid4()),
            sender_id="current_user",  # TODO: Get from session
            recipient_id=recipient_id,
            content=content,
            timestamp=datetime.utcnow(),
            message_type=message_type
        )
        
        # Add to pending messages
        self.pending_messages[message.id] = message
        
        # TODO: Encrypt message
        # TODO: Route through P2P network
        # TODO: Handle delivery confirmation
        
        logger.info(f"📤 Message sent: {message.id} -> {recipient_id}")
        return message.id
    
    async def receive_message(self, message: Message):
        """
        Process a received message.
        
        Args:
            message: The received message
        """
        # TODO: Decrypt message
        # TODO: Verify signature
        # TODO: Add to history
        
        # Call appropriate handler
        handler = self.message_handlers.get(message.message_type)
        if handler:
            await handler(message)
        
        self.message_history.append(message)
        logger.info(f"📥 Message received: {message.id} from {message.sender_id}")
    
    def get_message_history(self, peer_id: str) -> List[Message]:
        """Get message history with a specific peer."""
        return [
            msg for msg in self.message_history
            if msg.sender_id == peer_id or msg.recipient_id == peer_id
        ]
    
    def get_pending_messages(self) -> List[Message]:
        """Get list of pending messages."""
        return list(self.pending_messages.values())