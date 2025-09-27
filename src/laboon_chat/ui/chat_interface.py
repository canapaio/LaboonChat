"""
P2P Messaging Interface Components
=================================

React-like components for the decentralized P2P messaging web interface.
Integrates the dark creamy theme with security visual indicators.

🌐 Beautiful and secure, empowering individual responsibility 🌊
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Contact:
    """Contact with security indicators"""
    id: str
    name: str
    avatar: str
    key_type: str  # 'solid' or 'liquid'
    trust_level: int  # 0-100
    last_seen: str
    status: str  # 'online', 'away', 'offline'

@dataclass
class Message:
    """Message with security metadata"""
    id: str
    contact_id: str
    text: str
    sender: str  # 'me' or contact_id
    timestamp: str
    encrypted: bool = True
    verified: bool = True

class ChatInterface:
    """
    Main chat interface component manager.
    Handles UI state and integrates with MessageEngine.
    """
    
    def __init__(self):
        self.contacts: Dict[str, Contact] = {}
        self.messages: Dict[str, List[Message]] = {}
        self.active_contact: Optional[str] = None
        
    def add_contact(self, contact: Contact):
        """Add or update contact"""
        self.contacts[contact.id] = contact
        if contact.id not in self.messages:
            self.messages[contact.id] = []
    
    def add_message(self, message: Message):
        """Add message to conversation"""
        if message.contact_id not in self.messages:
            self.messages[message.contact_id] = []
        self.messages[message.contact_id].append(message)
    
    def get_contact_list_html(self) -> str:
        """Generate HTML for contact list with security indicators"""
        if not self.contacts:
            return '<div class="no-contacts">No contacts yet</div>'
        
        html_parts = []
        for contact in self.contacts.values():
            # Security icon based on key type
            if contact.key_type == 'solid':
                security_icon = '🔒'
                security_class = 'solid-key'
                security_color = '#d4af37'
            else:
                security_icon = '💧'
                security_class = 'liquid-key'
                security_color = '#4a9eff'
            
            # Trust level bar
            trust_width = contact.trust_level
            trust_color = self._get_trust_color(contact.trust_level)
            
            # Status indicator
            status_emoji = {
                'online': '🟢',
                'away': '🟡', 
                'offline': '⚫'
            }.get(contact.status, '⚫')
            
            contact_html = f"""
            <div class="contact-card {security_class}" data-contact-id="{contact.id}">
                <div class="contact-avatar">
                    {contact.avatar}
                    <div class="status-indicator">{status_emoji}</div>
                </div>
                <div class="contact-info">
                    <div class="contact-name">{contact.name}</div>
                    <div class="contact-meta">
                        <span class="security-indicator" style="color: {security_color}">
                            {security_icon}
                        </span>
                        <span class="last-seen">{contact.last_seen}</span>
                    </div>
                    <div class="trust-bar">
                        <div class="trust-fill" style="width: {trust_width}%; background: {trust_color}"></div>
                        <span class="trust-level">{contact.trust_level}%</span>
                    </div>
                </div>
            </div>
            """
            html_parts.append(contact_html)
        
        return ''.join(html_parts)
    
    def get_chat_header_html(self, contact_id: str) -> str:
        """Generate chat header with security info"""
        if contact_id not in self.contacts:
            return '<div class="chat-header">Select a contact</div>'
        
        contact = self.contacts[contact_id]
        
        # Security badge
        if contact.key_type == 'solid':
            security_badge = f"""
            <div class="security-badge solid">
                <span class="security-icon">🔒</span>
                <span class="security-text">Solid Key</span>
                <div class="security-pulse"></div>
            </div>
            """
        else:
            security_badge = f"""
            <div class="security-badge liquid">
                <span class="security-icon">💧</span>
                <span class="security-text">Liquid Key</span>
                <div class="security-wave"></div>
            </div>
            """
        
        return f"""
        <div class="chat-header">
            <div class="contact-info">
                <div class="contact-avatar">{contact.avatar}</div>
                <div class="contact-details">
                    <h3>{contact.name}</h3>
                    <p class="contact-status">{contact.status}</p>
                </div>
            </div>
            {security_badge}
            <div class="trust-indicator">
                <div class="trust-circle" style="--trust-level: {contact.trust_level}%">
                    <span>{contact.trust_level}%</span>
                </div>
            </div>
        </div>
        """
    
    def get_messages_html(self, contact_id: str) -> str:
        """Generate messages HTML for contact"""
        if contact_id not in self.messages:
            return '<div class="no-messages">Start a conversation!</div>'
        
        messages = self.messages[contact_id]
        if not messages:
            return '<div class="no-messages">Start a conversation!</div>'
        
        html_parts = []
        for message in messages:
            sender_class = 'sent' if message.sender == 'me' else 'received'
            
            # Security indicators
            encryption_icon = '🔐' if message.encrypted else '⚠️'
            verification_icon = '✅' if message.verified else '❌'
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(message.timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            except:
                time_str = 'now'
            
            message_html = f"""
            <div class="message {sender_class}">
                <div class="message-content">
                    <p>{message.text}</p>
                    <div class="message-meta">
                        <span class="message-time">{time_str}</span>
                        <span class="security-indicators">
                            <span title="Encrypted">{encryption_icon}</span>
                            <span title="Verified">{verification_icon}</span>
                        </span>
                    </div>
                </div>
            </div>
            """
            html_parts.append(message_html)
        
        return ''.join(html_parts)
    
    def _get_trust_color(self, trust_level: int) -> str:
        """Get color for trust level"""
        if trust_level >= 90:
            return '#4ade80'  # Green
        elif trust_level >= 70:
            return '#d4af37'  # Gold
        elif trust_level >= 50:
            return '#f59e0b'  # Orange
        else:
            return '#ef4444'  # Red
    
    def to_json_state(self) -> str:
        """Export current state as JSON for frontend"""
        state = {
            'contacts': {
                cid: {
                    'id': c.id,
                    'name': c.name,
                    'avatar': c.avatar,
                    'key_type': c.key_type,
                    'trust_level': c.trust_level,
                    'last_seen': c.last_seen,
                    'status': c.status
                } for cid, c in self.contacts.items()
            },
            'messages': {
                cid: [
                    {
                        'id': m.id,
                        'contact_id': m.contact_id,
                        'text': m.text,
                        'sender': m.sender,
                        'timestamp': m.timestamp,
                        'encrypted': m.encrypted,
                        'verified': m.verified
                    } for m in msgs
                ] for cid, msgs in self.messages.items()
            },
            'active_contact': self.active_contact
        }
        return json.dumps(state, indent=2)
    
    def from_json_state(self, json_str: str):
        """Import state from JSON"""
        try:
            state = json.loads(json_str)
            
            # Load contacts
            self.contacts = {}
            for cid, c_data in state.get('contacts', {}).items():
                self.contacts[cid] = Contact(**c_data)
            
            # Load messages
            self.messages = {}
            for cid, msgs_data in state.get('messages', {}).items():
                self.messages[cid] = [Message(**m_data) for m_data in msgs_data]
            
            self.active_contact = state.get('active_contact')
            
        except Exception as e:
            print(f"Error loading state: {e}")

# Demo data for testing
def create_demo_interface() -> ChatInterface:
    """Create demo interface with sample data"""
    interface = ChatInterface()
    
    # Add demo contacts
    interface.add_contact(Contact(
        id='alice',
        name='Alice',
        avatar='👩‍💻',
        key_type='solid',
        trust_level=95,
        last_seen='2 min ago',
        status='online'
    ))
    
    interface.add_contact(Contact(
        id='bob', 
        name='Bob',
        avatar='👨‍🔬',
        key_type='liquid',
        trust_level=78,
        last_seen='1 hour ago',
        status='away'
    ))
    
    # Add demo messages
    interface.add_message(Message(
        id='1',
        contact_id='alice',
        text='Hey! How are you?',
        sender='alice',
        timestamp='2024-01-27T10:00:00Z'
    ))
    
    interface.add_message(Message(
        id='2',
        contact_id='alice', 
        text='Great! Just testing P2P messaging 🌐',
        sender='me',
        timestamp='2024-01-27T10:01:00Z'
    ))
    
    return interface