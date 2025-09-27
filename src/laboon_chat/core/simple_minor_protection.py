"""
📧 Sistema Semplificato di Protezione Minori - Notifiche Email Periodiche
========================================================================

Sistema minimalista per la protezione dei minori basato su:
- Notifiche email periodiche con riepilogo utilizzo
- Timer configurabile (default 60 minuti)
- Responsabilità individuale
- Configurazione semplice nei settings

🛡️ "Semplicità e responsabilità individuale" 📨

Features:
- Invio email periodiche con riepilogo utilizzo
- Timer configurabile da 15 minuti a 24 ore
- Template email semplici e informativi
- Configurazione tramite settings dell'applicazione
- Logging minimo per privacy

Author: LaboonChat Team
License: GPL-3.0
"""

import os
import json
import asyncio
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time

try:
    from .simple_minor_protection_template import MinorProtectionEmailTemplate
except ImportError:
    from simple_minor_protection_template import MinorProtectionEmailTemplate

logger = logging.getLogger(__name__)


@dataclass
class UsageSession:
    """Sessione di utilizzo per il riepilogo"""
    start_time: datetime
    end_time: Optional[datetime] = None
    messages_sent: int = 0
    messages_received: int = 0
    contacts_interacted: List[str] = None
    
    def __post_init__(self):
        if self.contacts_interacted is None:
            self.contacts_interacted = []


@dataclass
class EmailNotificationConfig:
    """Configurazione per le notifiche email"""
    is_minor: bool = False  # Indica se l'utente è minorenne
    enabled: bool = True
    interval_minutes: int = 60  # Default 60 minuti
    parent_email: str = ""
    user_name: str = ""
    smtp_server: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = "protection@laboonchat.local"


class SimpleMinorProtection:
    """Sistema semplificato di protezione minori con notifiche email periodiche"""
    
    def __init__(self, data_dir: str = "simple_protection_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # File di configurazione
        self.config_file = self.data_dir / "protection_config.json"
        self.usage_file = self.data_dir / "usage_sessions.json"
        
        # Configurazione
        self.config = self._load_config()
        
        # Sessioni di utilizzo
        self.current_session: Optional[UsageSession] = None
        self.usage_history: List[UsageSession] = []
        self._load_usage_history()
        
        # Timer per notifiche
        self.notification_timer: Optional[threading.Timer] = None
        self.is_running = False
        
        logger.info("📧 Simple Minor Protection System initialized")
    
    def is_enabled(self) -> bool:
        """Verifica se il sistema di protezione è attivo"""
        return self.config.enabled
    
    def is_minor(self) -> bool:
        """Verifica se l'utente è configurato come minorenne"""
        return self.config.is_minor
    
    def set_minor_status(self, is_minor: bool, parent_email: str = "", user_name: str = ""):
        """
        Imposta lo stato di minorenne dell'utente
        
        Args:
            is_minor: True se l'utente è minorenne
            parent_email: Email del genitore (richiesta se is_minor=True)
            user_name: Nome dell'utente
        """
        self.config.is_minor = is_minor
        
        if is_minor:
            if not parent_email:
                raise ValueError("Email del genitore richiesta per utenti minorenni")
            self.config.parent_email = parent_email
            self.config.user_name = user_name
            # Attiva automaticamente la protezione per i minorenni
            self.config.enabled = True
            logger.info(f"👶 User set as minor: {user_name} - parent: {parent_email}")
        else:
            # Se non è più minorenne, disattiva la protezione
            if self.config.enabled:
                self.disable_protection("Utente diventato maggiorenne")
            logger.info(f"🔞 User set as adult: {user_name}")
        
        self._save_config()
    
    def enable_protection(self, parent_email: str, user_name: str = "", 
                         interval_minutes: int = 60, smtp_config: Dict = None):
        """
        Attiva il sistema di protezione minori
        
        Args:
            parent_email: Email del genitore per le notifiche
            user_name: Nome dell'utente (opzionale)
            interval_minutes: Intervallo notifiche in minuti (default 60)
            smtp_config: Configurazione SMTP (opzionale)
        """
        self.config.enabled = True
        self.config.parent_email = parent_email
        self.config.user_name = user_name
        self.config.interval_minutes = max(15, min(1440, interval_minutes))  # 15 min - 24 ore
        
        if smtp_config:
            self.config.smtp_server = smtp_config.get('server', self.config.smtp_server)
            self.config.smtp_port = smtp_config.get('port', self.config.smtp_port)
            self.config.smtp_username = smtp_config.get('username', self.config.smtp_username)
            self.config.smtp_password = smtp_config.get('password', self.config.smtp_password)
            self.config.from_email = smtp_config.get('from_email', self.config.from_email)
        
        self._save_config()
        logger.info(f"🛡️ Minor protection enabled for {user_name} - notifications to {parent_email}")
        
        # Invia email di attivazione
        self._send_activation_notification()
    
    def disable_protection(self, reason: str = "Utente diventato maggiorenne"):
        """
        Disattiva il sistema di protezione minori
        
        Args:
            reason: Motivo della disattivazione
        """
        if not self.config.enabled:
            logger.info("Protection already disabled")
            return
        
        # Invia notifica di disattivazione prima di disattivare
        self._send_deactivation_notification(reason)
        
        # Ferma il sistema
        self.stop()
        
        # Disattiva nelle configurazioni
        self.config.enabled = False
        self._save_config()
        
        logger.info(f"🔓 Minor protection disabled: {reason}")
    
    def update_config(self, **kwargs):
        """
        Aggiorna la configurazione del sistema
        
        Args:
            **kwargs: Parametri da aggiornare (parent_email, interval_minutes, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                if key == 'interval_minutes':
                    value = max(15, min(1440, value))  # Limiti: 15 min - 24 ore
                setattr(self.config, key, value)
        
        self._save_config()
        logger.info("📝 Protection config updated")
        
        # Riavvia il timer se necessario
        if self.is_running and self.config.enabled:
            self._restart_notification_timer()
    
    def _load_config(self) -> EmailNotificationConfig:
        """Carica configurazione dalle impostazioni"""
        default_config = {
            "is_minor": False,
            "enabled": False,
            "interval_minutes": 60,
            "parent_email": "",
            "user_name": "",
            "smtp_server": "localhost",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "from_email": "protection@laboonchat.local"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    default_config.update(config_data)
            except Exception as e:
                logger.warning(f"Failed to load protection config: {e}")
        
        return EmailNotificationConfig(**default_config)
    
    def _save_config(self):
        """Salva configurazione"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save protection config: {e}")
    
    def _load_usage_history(self):
        """Carica storico utilizzo"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.usage_history = []
                    for session_data in data:
                        session = UsageSession(
                            start_time=datetime.fromisoformat(session_data['start_time']),
                            end_time=datetime.fromisoformat(session_data['end_time']) if session_data.get('end_time') else None,
                            messages_sent=session_data.get('messages_sent', 0),
                            messages_received=session_data.get('messages_received', 0),
                            contacts_interacted=session_data.get('contacts_interacted', [])
                        )
                        self.usage_history.append(session)
            except Exception as e:
                logger.warning(f"Failed to load usage history: {e}")
                self.usage_history = []
    
    def _save_usage_history(self):
        """Salva storico utilizzo"""
        try:
            data = []
            for session in self.usage_history:
                session_data = {
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'messages_sent': session.messages_sent,
                    'messages_received': session.messages_received,
                    'contacts_interacted': session.contacts_interacted
                }
                data.append(session_data)
            
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage history: {e}")
    
    def update_config(self, **kwargs):
        """Aggiorna configurazione"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._save_config()
        
        # Riavvia timer se necessario
        if self.is_running:
            self.stop_monitoring()
            self.start_monitoring()
        
        logger.info(f"Protection config updated: {kwargs}")
    
    def start_session(self, user_name: str = ""):
        """Inizia una nuova sessione di utilizzo"""
        if self.current_session:
            self.end_session()
        
        self.current_session = UsageSession(
            start_time=datetime.now()
        )
        
        if user_name:
            self.config.user_name = user_name
            self._save_config()
        
        logger.info("📱 Usage session started")
    
    def end_session(self):
        """Termina la sessione corrente"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.usage_history.append(self.current_session)
            self._save_usage_history()
            
            logger.info("📱 Usage session ended")
            self.current_session = None
    
    def log_message_sent(self, contact: str = ""):
        """Registra messaggio inviato"""
        if self.current_session:
            self.current_session.messages_sent += 1
            if contact and contact not in self.current_session.contacts_interacted:
                self.current_session.contacts_interacted.append(contact)
    
    def log_message_received(self, contact: str = ""):
        """Registra messaggio ricevuto"""
        if self.current_session:
            self.current_session.messages_received += 1
            if contact and contact not in self.current_session.contacts_interacted:
                self.current_session.contacts_interacted.append(contact)
    
    def start_monitoring(self):
        """Avvia monitoraggio con notifiche periodiche"""
        if not self.config.enabled or not self.config.parent_email:
            logger.info("📧 Email notifications disabled or no parent email configured")
            return
        
        self.is_running = True
        self._schedule_next_notification()
        logger.info(f"📧 Email monitoring started - interval: {self.config.interval_minutes} minutes")
    
    def stop_monitoring(self):
        """Ferma monitoraggio"""
        self.is_running = False
        if self.notification_timer:
            self.notification_timer.cancel()
            self.notification_timer = None
        logger.info("📧 Email monitoring stopped")
    
    def _schedule_next_notification(self):
        """Programma prossima notifica"""
        if not self.is_running:
            return
        
        interval_seconds = self.config.interval_minutes * 60
        self.notification_timer = threading.Timer(interval_seconds, self._send_periodic_notification)
        self.notification_timer.start()
    
    def _send_periodic_notification(self):
        """Invia notifica periodica"""
        try:
            if self.config.enabled and self.config.parent_email:
                self._send_usage_summary_email()
            
            # Programma prossima notifica
            self._schedule_next_notification()
            
        except Exception as e:
            logger.error(f"Error sending periodic notification: {e}")
            # Riprova tra 5 minuti in caso di errore
            if self.is_running:
                self.notification_timer = threading.Timer(300, self._send_periodic_notification)
                self.notification_timer.start()
    
    def _send_usage_summary_email(self):
        """Invia email con riepilogo utilizzo"""
        try:
            # Calcola statistiche periodo corrente
            now = datetime.now()
            period_start = now - timedelta(minutes=self.config.interval_minutes)
            
            # Sessioni nel periodo
            period_sessions = [
                s for s in self.usage_history 
                if s.start_time >= period_start
            ]
            
            # Aggiungi sessione corrente se attiva
            if self.current_session and self.current_session.start_time >= period_start:
                current_copy = UsageSession(
                    start_time=self.current_session.start_time,
                    end_time=now,
                    messages_sent=self.current_session.messages_sent,
                    messages_received=self.current_session.messages_received,
                    contacts_interacted=self.current_session.contacts_interacted.copy()
                )
                period_sessions.append(current_copy)
            
            # Calcola totali
            total_messages_sent = sum(s.messages_sent for s in period_sessions)
            total_messages_received = sum(s.messages_received for s in period_sessions)
            all_contacts = set()
            for s in period_sessions:
                all_contacts.update(s.contacts_interacted)
            
            # Calcola tempo totale di utilizzo
            total_minutes = 0
            for session in period_sessions:
                if session.end_time:
                    duration = session.end_time - session.start_time
                    total_minutes += duration.total_seconds() / 60
            
            # Crea email usando template
            subject = MinorProtectionEmailTemplate.generate_subject(
                self.config.user_name or 'Utente',
                self.config.interval_minutes
            )
            
            # Genera contenuto email usando template
            body = MinorProtectionEmailTemplate.generate_usage_summary_text(
                self.config.user_name or 'Utente',
                self.current_session,
                period_sessions,
                self.config.interval_minutes
            )
            
            self._send_email(subject, body)
            logger.info(f"📧 Usage summary email sent to {self.config.parent_email}")
            
        except Exception as e:
            logger.error(f"Failed to send usage summary email: {e}")
    
    def _create_email_template(self, **kwargs) -> str:
        """Crea template email per riepilogo"""
        return f"""
🛡️ RIEPILOGO UTILIZZO LABOONCHAT

👤 Utente: {self.config.user_name or 'Non specificato'}
📅 Periodo: {kwargs['period_start'].strftime('%H:%M')} - {kwargs['period_end'].strftime('%H:%M')}
⏱️ Durata monitoraggio: {self.config.interval_minutes} minuti

📊 STATISTICHE UTILIZZO:
• ⏰ Tempo totale utilizzo: {kwargs['usage_minutes']} minuti
• 📤 Messaggi inviati: {kwargs['total_messages_sent']}
• 📥 Messaggi ricevuti: {kwargs['total_messages_received']}
• 👥 Contatti interagiti: {kwargs['contacts_count']}
• 🔄 Sessioni attive: {kwargs['sessions_count']}

🔧 CONFIGURAZIONE:
• 📧 Frequenza notifiche: ogni {self.config.interval_minutes} minuti
• 🛡️ Sistema: Protezione Minori Semplificata
• 📱 Responsabilità: Individuale

ℹ️ INFORMAZIONI:
Questa è una notifica automatica del sistema di protezione minori semplificato.
Il sistema si basa sulla responsabilità individuale e fornisce solo un riepilogo
periodico dell'utilizzo senza controlli invasivi.

Per modificare la frequenza delle notifiche, accedere alle impostazioni
dell'applicazione nella sezione "Protezione Minori".

---
Sistema LaboonChat - Protezione Minori Semplificata
Generato automaticamente il {kwargs['period_end'].strftime('%d/%m/%Y alle %H:%M')}
        """.strip()
    
    def _send_activation_notification(self):
        """Invia notifica di attivazione del sistema"""
        try:
            subject = f"🛡️ Protezione Minori Attivata - {self.config.user_name or 'LaboonChat'}"
            
            body = f"""
🛡️ SISTEMA DI PROTEZIONE MINORI ATTIVATO

👤 Utente: {self.config.user_name or 'Non specificato'}
📧 Email notifiche: {self.config.parent_email}
⏱️ Frequenza notifiche: ogni {self.config.interval_minutes} minuti
📅 Data attivazione: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}

🔧 CONFIGURAZIONE:
• Sistema: Protezione Minori Semplificata
• Tipo: Notifiche email periodiche
• Responsabilità: Individuale
• Privacy: Logging minimo

ℹ️ INFORMAZIONI:
Il sistema di protezione minori è stato attivato con successo.
Riceverai notifiche periodiche con un riepilogo dell'utilizzo dell'applicazione.

Il sistema si basa sulla responsabilità individuale e non applica controlli invasivi.
Le notifiche possono essere configurate dalle impostazioni dell'applicazione.

---
Sistema LaboonChat - Protezione Minori Semplificata
            """.strip()
            
            self._send_email(subject, body)
            logger.info("📧 Activation notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send activation notification: {e}")
    
    def _send_deactivation_notification(self, reason: str):
        """Invia notifica di disattivazione del sistema"""
        try:
            subject = f"🔓 Protezione Minori Disattivata - {self.config.user_name or 'LaboonChat'}"
            
            body = f"""
🔓 SISTEMA DI PROTEZIONE MINORI DISATTIVATO

👤 Utente: {self.config.user_name or 'Non specificato'}
📧 Email notifiche: {self.config.parent_email}
📅 Data disattivazione: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}
💬 Motivo: {reason}

ℹ️ INFORMAZIONI:
Il sistema di protezione minori è stato disattivato.
Non riceverai più notifiche periodiche sull'utilizzo dell'applicazione.

Se la disattivazione è avvenuta perché l'utente è diventato maggiorenne,
congratulazioni per questo importante traguardo! 🎉

Il sistema può essere riattivato in qualsiasi momento dalle impostazioni
dell'applicazione se necessario.

---
Sistema LaboonChat - Protezione Minori Semplificata
            """.strip()
            
            self._send_email(subject, body)
            logger.info("📧 Deactivation notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send deactivation notification: {e}")
    
    def _restart_notification_timer(self):
        """Riavvia il timer delle notifiche"""
        if self.notification_timer:
            self.notification_timer.cancel()
        
        if self.is_running and self.config.enabled:
            self._schedule_next_notification()
    
    def start(self):
        """Avvia il sistema (alias per start_monitoring)"""
        self.start_monitoring()
    
    def stop(self):
        """Ferma il sistema (alias per stop_monitoring)"""
        self.stop_monitoring()
    
    def _send_email(self, subject: str, body: str):
        """Invia email utilizzando configurazione SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_user
            msg['To'] = self.config.parent_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Connessione SMTP
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.smtp_port == 587:
                    server.starttls()
                
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                
                server.send_message(msg)
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Ottieni configurazione come dizionario"""
        return asdict(self.config)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche utilizzo"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Sessioni di oggi
        today_sessions = [
            s for s in self.usage_history 
            if s.start_time >= today_start
        ]
        
        # Aggiungi sessione corrente se attiva
        if self.current_session and self.current_session.start_time >= today_start:
            today_sessions.append(self.current_session)
        
        # Calcola statistiche
        total_messages_sent = sum(s.messages_sent for s in today_sessions)
        total_messages_received = sum(s.messages_received for s in today_sessions)
        
        all_contacts = set()
        for s in today_sessions:
            all_contacts.update(s.contacts_interacted)
        
        return {
            'today_sessions': len(today_sessions),
            'today_messages_sent': total_messages_sent,
            'today_messages_received': total_messages_received,
            'today_contacts': len(all_contacts),
            'current_session_active': self.current_session is not None,
            'monitoring_active': self.is_running,
            'next_notification_minutes': self.config.interval_minutes if self.is_running else None
        }


# Singleton instance
_simple_protection_instance = None

def get_simple_protection() -> SimpleMinorProtection:
    """Ottieni istanza singleton del sistema di protezione semplificato"""
    global _simple_protection_instance
    if _simple_protection_instance is None:
        _simple_protection_instance = SimpleMinorProtection()
    return _simple_protection_instance