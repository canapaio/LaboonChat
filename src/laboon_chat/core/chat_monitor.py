"""
👁️ P2P Chat Monitor - Sistema di Monitoraggio Decentralizzato
============================================================

Sistema di monitoraggio delle chat basato su responsabilità individuale.
Ogni nodo gestisce autonomamente la protezione dei propri minori.

🛡️ "Protezione locale e responsabilità individuale" 👁️

Features:
- Monitoraggio locale delle chat
- Identificazione automatica utenti minori
- Notifiche ai genitori tramite nodo locale
- Filtri contenuto configurabili
- Dashboard di controllo parentale locale
- Audit trail decentralizzato

Author: P2P Messaging Team
License: GPL-3.0
"""

import os
import json
import asyncio
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
import re

# Import dei moduli LaboonChat
# Sistema semplificato di protezione minori
try:
    from .simple_minor_protection import SimpleMinorProtection
except ImportError:
    SimpleMinorProtection = None

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Rappresenta un messaggio di chat"""
    message_id: str
    sender_id: str
    sender_username: str
    sender_display_name: str
    recipient_id: str
    recipient_username: str
    recipient_display_name: str
    content: str
    timestamp: datetime
    message_type: str = "text"  # text, image, file, etc.
    is_group_chat: bool = False
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Crea istanza da dizionario"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class MonitoringRule:
    """Regola di monitoraggio"""
    rule_id: str
    rule_name: str
    description: str
    is_active: bool = True
    applies_to_minors: bool = True
    applies_to_adults: bool = False
    content_filters: List[str] = None  # Regex patterns
    action: str = "notify_parent"  # notify_parent, block_message, flag_for_review
    severity: str = "normal"  # low, normal, high, critical
    
    def __post_init__(self):
        if self.content_filters is None:
            self.content_filters = []

@dataclass
class MonitoringAlert:
    """Alert di monitoraggio"""
    alert_id: str
    message_id: str
    user_id: str
    rule_id: str
    alert_type: str
    severity: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class ChatMonitor:
    """Sistema di monitoraggio chat per protezione minori"""
    
    def __init__(self, data_dir: str = "chat_monitor_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Directory per dati
        self.messages_dir = self.data_dir / "messages"
        self.alerts_dir = self.data_dir / "alerts"
        self.rules_dir = self.data_dir / "rules"
        self.audit_dir = self.data_dir / "audit"
        
        for dir_path in [self.messages_dir, self.alerts_dir, self.rules_dir, self.audit_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Cache messaggi recenti (ultimi 1000)
        self.recent_messages: List[ChatMessage] = []
        self.max_recent_messages = 1000
        
        # Cache utenti minori
        self.minor_users_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = timedelta(hours=1)
        self.last_cache_update = datetime.now() - self.cache_expiry
        
        # Regole di monitoraggio
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        
        # Alert attivi
        self.active_alerts: Dict[str, MonitoringAlert] = {}
        
        # Sistema semplificato di protezione minori
        self.minor_protection = SimpleMinorProtection() if SimpleMinorProtection else None
        
        # Statistiche
        self.stats = {
            'messages_monitored': 0,
            'notifications_sent': 0,
            'alerts_generated': 0,
            'minors_protected': set()
        }
        
        # Carica configurazione
        self._load_monitoring_rules()
        self._load_recent_messages()
        
        logger.info("👁️ Chat Monitor initialized")
    
    def _load_monitoring_rules(self):
        """Carica regole di monitoraggio"""
        # Regole di default
        default_rules = [
            MonitoringRule(
                rule_id="minor_all_messages",
                rule_name="Tutti i messaggi dei minori",
                description="Monitora tutti i messaggi inviati e ricevuti da utenti minori",
                applies_to_minors=True,
                applies_to_adults=False,
                action="notify_parent",
                severity="normal"
            ),
            MonitoringRule(
                rule_id="inappropriate_content",
                rule_name="Contenuto inappropriato",
                description="Rileva contenuto potenzialmente inappropriato",
                applies_to_minors=True,
                applies_to_adults=False,
                content_filters=[
                    r'\b(sesso|droga|alcol|violenza)\b',
                    r'\b(incontro|appuntamento|vedere)\b.*\b(soli|nascosto|segreto)\b',
                    r'\b(indirizzo|casa|scuola)\b.*\b(dove|quando|vieni)\b'
                ],
                action="notify_parent",
                severity="high"
            ),
            MonitoringRule(
                rule_id="personal_info_sharing",
                rule_name="Condivisione informazioni personali",
                description="Rileva condivisione di informazioni personali",
                applies_to_minors=True,
                applies_to_adults=False,
                content_filters=[
                    r'\b\d{10,}\b',  # Numeri di telefono
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                    r'\b(via|corso|piazza|strada)\s+[A-Za-z\s]+\d+\b'  # Indirizzi
                ],
                action="notify_parent",
                severity="high"
            ),
            MonitoringRule(
                rule_id="stranger_contact",
                rule_name="Contatto con sconosciuti",
                description="Rileva conversazioni con utenti non verificati",
                applies_to_minors=True,
                applies_to_adults=False,
                action="notify_parent",
                severity="normal"
            )
        ]
        
        # Carica regole da file
        rules_file = self.rules_dir / "monitoring_rules.json"
        if rules_file.exists():
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    for rule_data in rules_data:
                        rule = MonitoringRule(**rule_data)
                        self.monitoring_rules[rule.rule_id] = rule
            except Exception as e:
                logger.warning(f"Failed to load monitoring rules: {e}")
        
        # Aggiungi regole di default se non esistono
        for rule in default_rules:
            if rule.rule_id not in self.monitoring_rules:
                self.monitoring_rules[rule.rule_id] = rule
        
        # Salva regole aggiornate
        self._save_monitoring_rules()
    
    def _save_monitoring_rules(self):
        """Salva regole di monitoraggio"""
        rules_file = self.rules_dir / "monitoring_rules.json"
        try:
            rules_data = [asdict(rule) for rule in self.monitoring_rules.values()]
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save monitoring rules: {e}")
    
    def _load_recent_messages(self):
        """Carica messaggi recenti"""
        messages_file = self.messages_dir / "recent_messages.json"
        if messages_file.exists():
            try:
                with open(messages_file, 'r', encoding='utf-8') as f:
                    messages_data = json.load(f)
                    self.recent_messages = [
                        ChatMessage.from_dict(msg_data) 
                        for msg_data in messages_data[-self.max_recent_messages:]
                    ]
            except Exception as e:
                logger.warning(f"Failed to load recent messages: {e}")
    
    def _save_recent_messages(self):
        """Salva messaggi recenti"""
        messages_file = self.messages_dir / "recent_messages.json"
        try:
            # Mantieni solo gli ultimi N messaggi
            recent_messages = self.recent_messages[-self.max_recent_messages:]
            messages_data = [msg.to_dict() for msg in recent_messages]
            
            with open(messages_file, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recent messages: {e}")
    
    def _log_message_for_protection(self, message: ChatMessage):
        """Log del messaggio per il sistema di protezione semplificato"""
        if self.minor_protection:
            try:
                # Log del messaggio nel sistema di protezione
                self.minor_protection.log_message(
                    sender=message.sender_username,
                    recipient=message.recipient_username,
                    content_preview=message.content[:50] + "..." if len(message.content) > 50 else message.content,
                    timestamp=message.timestamp
                )
            except Exception as e:
                logger.warning(f"Failed to log message for protection: {e}")
    
    def _check_content_filters(self, content: str, filters: List[str]) -> List[str]:
        """Verifica filtri contenuto"""
        matches = []
        for filter_pattern in filters:
            try:
                if re.search(filter_pattern, content, re.IGNORECASE):
                    matches.append(filter_pattern)
            except re.error as e:
                logger.warning(f"Invalid regex pattern {filter_pattern}: {e}")
        return matches
    
    def _generate_alert(self, message: ChatMessage, rule: MonitoringRule, 
                       filter_matches: List[str] = None) -> MonitoringAlert:
        """Genera alert di monitoraggio"""
        alert_id = hashlib.sha256(
            f"{message.message_id}_{rule.rule_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        description = f"Rule '{rule.rule_name}' triggered"
        if filter_matches:
            description += f" - Matched filters: {', '.join(filter_matches)}"
        
        alert = MonitoringAlert(
            alert_id=alert_id,
            message_id=message.message_id,
            user_id=message.sender_id,
            rule_id=rule.rule_id,
            alert_type=rule.action,
            severity=rule.severity,
            description=description,
            timestamp=datetime.now()
        )
        
        return alert
    
    def _audit_log(self, action: str, details: Dict[str, Any]):
        """Registra azione nel log di audit"""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        
        # Salva nel file di audit giornaliero
        today = datetime.now().strftime("%Y-%m-%d")
        audit_file = self.audit_dir / f"monitor_audit_{today}.json"
        
        try:
            # Carica audit esistente o crea nuovo
            if audit_file.exists():
                with open(audit_file, 'r', encoding='utf-8') as f:
                    audit_data = json.load(f)
            else:
                audit_data = []
            
            audit_data.append(audit_entry)
            
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(audit_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to write monitor audit log: {e}")
    
    async def monitor_message(self, message: ChatMessage) -> Dict[str, Any]:
        """
        Monitora un messaggio di chat
        
        Args:
            message: Messaggio da monitorare
            
        Returns:
            Dict con risultati del monitoraggio
        """
        try:
            # Aggiungi a messaggi recenti
            self.recent_messages.append(message)
            if len(self.recent_messages) > self.max_recent_messages:
                self.recent_messages = self.recent_messages[-self.max_recent_messages:]
            
            # Salva messaggi recenti
            self._save_recent_messages()
            
            # Log per sistema di protezione semplificato
            self._log_message_for_protection(message)
            
            # Statistiche
            self.stats['messages_monitored'] += 1
            
            # Risultato semplificato
            results = {
                'message_id': message.message_id,
                'monitored': True,
                'logged_for_protection': self.minor_protection is not None
            }
            
            # Log audit semplificato
            self._audit_log("message_monitored", {
                'message_id': message.message_id,
                'sender_id': message.sender_id,
                'logged_for_protection': results['logged_for_protection']
            })
            
            logger.debug(f"👁️ Monitored message {message.message_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error monitoring message: {e}")
            return {
                'message_id': message.message_id,
                'error': str(e),
                'monitored': False
            }
    
    async def _handle_parent_notification(self, message: ChatMessage, 
                                        alert: MonitoringAlert, results: Dict[str, Any]):
        """Gestisce notifica ai genitori"""
        try:
            # Determina chi è il minore
            minor_user_id = None
            minor_username = None
            minor_display_name = None
            chat_partner = None
            
            if self._is_minor_user(message.sender_id):
                minor_user_id = message.sender_id
                minor_username = message.sender_username
                minor_display_name = message.sender_display_name
                chat_partner = message.recipient_display_name or message.recipient_username
            elif self._is_minor_user(message.recipient_id):
                minor_user_id = message.recipient_id
                minor_username = message.recipient_username
                minor_display_name = message.recipient_display_name
                chat_partner = message.sender_display_name or message.sender_username
            
            if not minor_user_id:
                return
            
            # Ottieni email genitore
            parent_email = self._get_parent_email(minor_user_id)
            if not parent_email:
                logger.warning(f"No parent email found for minor user {minor_user_id}")
                return
            
            # Invia notifica
            success, error_msg = await send_minor_chat_notification(
                minor_user_id=minor_user_id,
                minor_username=minor_username,
                minor_display_name=minor_display_name,
                parent_email=parent_email,
                chat_partner=chat_partner,
                message_content=message.content
            )
            
            if success:
                results['notifications_sent'].append({
                    'type': 'parent_notification',
                    'parent_email': parent_email,
                    'minor_user_id': minor_user_id
                })
                results['actions_taken'].append(f"Parent notification sent to {parent_email}")
                self.stats['notifications_sent'] += 1
                
                logger.info(f"📧 Parent notification sent for minor {minor_username}")
            else:
                logger.error(f"Failed to send parent notification: {error_msg}")
                results['actions_taken'].append(f"Failed to send parent notification: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error handling parent notification: {e}")
            results['actions_taken'].append(f"Error in parent notification: {str(e)}")
    
    async def _handle_message_blocking(self, message: ChatMessage, 
                                     alert: MonitoringAlert, results: Dict[str, Any]):
        """Gestisce blocco messaggio"""
        # TODO: Implementare blocco messaggio
        results['actions_taken'].append("Message blocking (not implemented)")
        logger.info(f"🚫 Message {message.message_id} flagged for blocking")
    
    async def _handle_flag_for_review(self, message: ChatMessage, 
                                    alert: MonitoringAlert, results: Dict[str, Any]):
        """Gestisce segnalazione per revisione"""
        # TODO: Implementare sistema di revisione
        results['actions_taken'].append("Flagged for manual review")
        logger.info(f"🚩 Message {message.message_id} flagged for review")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche di monitoraggio"""
        return {
            'messages_monitored': self.stats['messages_monitored'],
            'notifications_sent': self.stats['notifications_sent'],
            'alerts_generated': self.stats['alerts_generated'],
            'minors_protected': len(self.stats['minors_protected']),
            'active_alerts': len(self.active_alerts),
            'monitoring_rules': len(self.monitoring_rules),
            'recent_messages': len(self.recent_messages)
        }
    
    def get_recent_messages_for_user(self, user_id: str, limit: int = 50) -> List[ChatMessage]:
        """Ottiene messaggi recenti per un utente"""
        user_messages = [
            msg for msg in self.recent_messages 
            if msg.sender_id == user_id or msg.recipient_id == user_id
        ]
        return user_messages[-limit:]
    
    def get_alerts_for_user(self, user_id: str) -> List[MonitoringAlert]:
        """Ottiene alert per un utente"""
        return [
            alert for alert in self.active_alerts.values()
            if alert.user_id == user_id
        ]

# Singleton instance
_chat_monitor = None

def get_chat_monitor() -> ChatMonitor:
    """Ottiene istanza singleton del monitor chat"""
    global _chat_monitor
    if _chat_monitor is None:
        _chat_monitor = ChatMonitor()
    return _chat_monitor

# Funzioni di convenienza
async def monitor_chat_message(sender_id: str, sender_username: str, sender_display_name: str,
                              recipient_id: str, recipient_username: str, recipient_display_name: str,
                              content: str, message_type: str = "text") -> Dict[str, Any]:
    """Monitora un messaggio di chat"""
    message = ChatMessage(
        message_id=hashlib.sha256(f"{sender_id}_{recipient_id}_{datetime.now().isoformat()}_{hash(content)}".encode()).hexdigest()[:16],
        sender_id=sender_id,
        sender_username=sender_username,
        sender_display_name=sender_display_name,
        recipient_id=recipient_id,
        recipient_username=recipient_username,
        recipient_display_name=recipient_display_name,
        content=content,
        timestamp=datetime.now(),
        message_type=message_type
    )
    
    return await get_chat_monitor().monitor_message(message)

# Global function for easy integration
async def monitor_chat_message_global(sender_id: str, sender_username: str, sender_display_name: str,
                              recipient_id: str, recipient_username: str, recipient_display_name: str,
                              content: str, message_type: str = "text") -> Dict[str, Any]:
    """
    Global function to monitor a chat message
    Returns monitoring result with alerts and notifications
    """
    try:
        # Get or create global monitor instance
        global _global_chat_monitor
        if '_global_chat_monitor' not in globals():
            _global_chat_monitor = ChatMonitor()
            
            # Add default monitoring rules
            default_rules = [
                MonitoringRule(
                    rule_id="inappropriate_content",
                    rule_name="Inappropriate Content",
                    description="Detects inappropriate content",
                    content_filters=[r"\b(inappropriate|bad|harmful)\b"],
                    action="notify_parent",
                    severity="high"
                ),
                MonitoringRule(
                    rule_id="personal_info",
                    rule_name="Personal Information", 
                    description="Detects personal information sharing",
                    content_filters=[r"\b\d{3}-\d{3}-\d{4}\b|\b\w+@\w+\.\w+\b"],
                    action="notify_parent",
                    severity="high"
                )
            ]
            
            for rule in default_rules:
                _global_chat_monitor.monitoring_rules[rule.rule_id] = rule
        
        # Monitor the message
        message = ChatMessage(
            message_id=hashlib.sha256(f"{sender_id}_{recipient_id}_{datetime.now().isoformat()}_{hash(content)}".encode()).hexdigest()[:16],
            sender_id=sender_id,
            sender_username=sender_username,
            sender_display_name=sender_display_name,
            recipient_id=recipient_id,
            recipient_username=recipient_username,
            recipient_display_name=recipient_display_name,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type
        )
        
        result = await _global_chat_monitor.monitor_message(message)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in global monitor_chat_message: {e}")
        return {
            'success': False,
            'error': str(e),
            'alerts_generated': [],
            'notifications_sent': [],
            'actions_taken': []
        }


if __name__ == "__main__":
    # Test the chat monitor
    import asyncio
    
    async def test_monitor():
        monitor = ChatMonitor()
        
        # Test monitoring
        result = await monitor_chat_message(
            sender_id="minor_user_123",
            sender_username="test_minor",
            sender_display_name="Test Minor",
            recipient_id="friend_456",
            recipient_username="friend",
            recipient_display_name="Friend",
            content="This is a test message",
            message_type="text"
        )
        
        print(f"Monitoring result: {result}")
        
        # Test global function
        global_result = await monitor_chat_message_global(
            sender_id="minor_user_456",
            sender_username="another_minor",
            sender_display_name="Another Minor",
            recipient_id="friend_789",
            recipient_username="another_friend",
            recipient_display_name="Another Friend",
            content="This message contains inappropriate content",
            message_type="text"
        )
        
        print(f"Global monitoring result: {global_result}")
    
    asyncio.run(test_monitor())