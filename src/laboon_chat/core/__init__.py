"""🌐 Decentralized P2P Core - Cuore dell'Applicazione
==================================================

Core minimo funzionante per messaggistica P2P decentralizzata con architettura plugin-first.
Integra crittografia, identità, messaggistica e gestione plugin sicura.

🔗 "Il cuore digitale che batte nella rete della comunicazione libera" 🌐

Author: Torrent-MSG Team
License: GPL-3.0
Version: 1.0.0
"""

import asyncio
import time
import signal
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import componenti core esistenti
from .config import Config
from .logger import Logger

# Import nuovo core minimo
from .crypto_core import LaboonCrypto, SecureStorage
from .identity import IdentityManager, IdentityInfo
from .messaging import LaboonMessaging, Message, PeerInfo
from .plugin_manager import LaboonPluginManager, PluginInterface


class P2PCoreAPI:
    """
    🌐 API del Core P2P per Plugin
    
    Fornisce interfaccia sicura per plugin per accedere
    alle funzionalità del core decentralizzato.
    """
    
    def __init__(self, core: 'P2PCore'):
        """
        Inizializza API
        
        Args:
            core: Istanza core P2P decentralizzato
        """
        self.core = core
    
    def get_identity(self) -> Optional[IdentityInfo]:
        """Ottiene identità corrente"""
        return self.core.identity_manager.get_current_identity()
    
    def send_message(self, recipient_hash: str, content: str, message_type: str = "text") -> bool:
        """Invia messaggio"""
        return self.core.messaging.send_message(recipient_hash, content, message_type)
    
    def get_messages(self, peer_hash: Optional[str] = None) -> List[Message]:
        """Ottiene messaggi"""
        return self.core.messaging.get_messages(peer_hash)
    
    def get_peers(self) -> List[PeerInfo]:
        """Ottiene peer conosciuti"""
        return self.core.messaging.get_peers()
    
    def encrypt_data(self, data: bytes, password: str) -> Optional[bytes]:
        """Critta dati"""
        encrypted = LaboonCrypto.encrypt_data(data, password)
        return encrypted.ciphertext if encrypted else None
    
    def hash_data(self, data: bytes) -> bytes:
        """Hash dati"""
        return LaboonCrypto.hash_data(data)
    
    def log_info(self, message: str):
        """Log informativo"""
        self.core.logger.info(f"[Plugin] {message}")
    
    def log_error(self, message: str):
        """Log errore"""
        self.core.logger.error(f"[Plugin] {message}")


class P2PCore:
    """
    🌐 Core principale P2P decentralizzato
    
    Nodo locale che coordina tutti i componenti:
    - Gestione identità crittografiche
    - Motore messaggistica P2P
    - Sistema plugin sicuro
    - Configurazione e logging
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inizializza core P2P decentralizzato
        
        Args:
            config_path: Percorso file configurazione
        """
        # Configurazione e logging
        self.config = Config(config_path)
        self.logger = Logger(self.config)
        
        # Componenti core
        self.identity_manager = IdentityManager()
        self.messaging: Optional[LaboonMessaging] = None
        self.plugin_manager: Optional[LaboonPluginManager] = None
        self.security_dashboard = None
        self.secure_boot_manager = None
        self.minor_protection = None
        
        # API per plugin
        self.core_api = P2PCoreAPI(self)
        
        # Stato applicazione
        self.is_running = False
        self.startup_time: Optional[float] = None
        
        # Callbacks
        self.message_received_callback = None
        self.peer_discovered_callback = None
        
        self.logger.info("🌐 P2P Core inizializzato")
    
    def initialize(self, display_name: str = "Laboon User") -> bool:
        """
        Inizializza tutti i componenti del core
        
        Args:
            display_name: Nome utente di default
            
        Returns:
            bool: True se inizializzazione riuscita
        """
        try:
            self.startup_time = time.time()
            self.logger.info("🚀 Avvio P2P Core decentralizzato...")
            
            # 0. Inizializza dashboard sicurezza
            from .security_dashboard import create_security_dashboard
            security_data_dir = self.config.get('security.data_dir', 'security_data')
            self.security_dashboard = create_security_dashboard(Path(security_data_dir))
            self.logger.info("🔐 Security Dashboard inizializzata")
            
            # 1. Assicura identità utente
            identity_hash = self.identity_manager.ensure_identity(display_name)
            identity = self.identity_manager.get_current_identity()
            
            if identity:
                self.logger.info(f"👤 Identità caricata: {identity.display_name} ({identity_hash[:16]}...)")
            else:
                self.logger.error("❌ Impossibile caricare identità")
                return False
            
            # 2. Inizializza motore messaggistica
            dht_port = self.config.get('network.dht_port', 6881)
            self.messaging = LaboonMessaging(dht_port)
            
            # Setup callbacks messaggistica
            self.messaging.message_received_callback = self._on_message_received
            self.messaging.peer_discovered_callback = self._on_peer_discovered
            
            if not self.messaging.start():
                self.logger.error("❌ Impossibile avviare motore messaggistica")
                return False
            
            self.logger.info(f"💬 Motore messaggistica avviato (porta {dht_port})")
            
            # 3. Inizializza gestore plugin con boot sicuro
            plugins_dir = self.config.get('plugins.directory')
            self.plugin_manager = LaboonPluginManager(plugins_dir)
            self.plugin_manager.set_core_api(self.core_api)
            
            # Setup callbacks plugin
            self.plugin_manager.plugin_loaded_callback = self._on_plugin_loaded
            self.plugin_manager.plugin_error_callback = self._on_plugin_error
            
            # 🔐 BOOT SICURO: Inizializza sistema boot verification
            from .secure_boot import initialize_secure_boot
            from .security_dashboard import SecurityLevel, SystemSecurityMetrics
            
            try:
                # Esegui boot sicuro asincrono
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                self.secure_boot_manager = loop.run_until_complete(
                    initialize_secure_boot(self.plugin_manager)
                )
                
                loop.close()
                
                # Ottieni statistiche boot
                stats = self.secure_boot_manager.boot_stats
                self.logger.info(f"🔐 Boot sicuro completato:")
                self.logger.info(f"   ✅ Plugin autorizzati: {stats['plugins_allowed']}")
                self.logger.info(f"   🔒 Plugin in quarantena: {stats['plugins_quarantined']}")
                self.logger.info(f"   🚫 Plugin bloccati: {stats['plugins_blocked']}")
                
                # Aggiorna dashboard sicurezza con metriche boot
                boot_duration = time.time() - self.startup_time
                system_metrics = SystemSecurityMetrics(
                    overall_security_level=SecurityLevel.SAFE if stats['plugins_blocked'] == 0 else SecurityLevel.MEDIUM,
                    total_plugins=stats['plugins_allowed'] + stats['plugins_quarantined'] + stats['plugins_blocked'],
                    certified_plugins=stats['plugins_allowed'],
                    quarantined_plugins=stats['plugins_quarantined'],
                    blocked_plugins=stats['plugins_blocked'],
                    active_threats=stats['plugins_blocked'],
                    resolved_threats=0,
                    last_scan_time=time.time(),
                    uptime=boot_duration,
                    boot_verification_status="COMPLETED"
                )
                self.security_dashboard.update_system_metrics(system_metrics)
                
            except Exception as e:
                self.logger.error(f"❌ Errore boot sicuro: {e}")
                # Fallback al caricamento standard
                essential_count = self.plugin_manager.auto_load_essential_plugins()
                self.logger.warning(f"⚠️ Fallback: Plugin essenziali caricati: {essential_count}")
                
                # Aggiorna dashboard con fallback
                if self.security_dashboard:
                    system_metrics = SystemSecurityMetrics(
                        overall_security_level=SecurityLevel.MEDIUM,
                        total_plugins=essential_count,
                        certified_plugins=0,
                        quarantined_plugins=0,
                        blocked_plugins=0,
                        active_threats=1,  # Errore boot sicuro
                        resolved_threats=0,
                        last_scan_time=time.time(),
                        uptime=time.time() - self.startup_time,
                        boot_verification_status="FALLBACK"
                    )
                    self.security_dashboard.update_system_metrics(system_metrics)
            
            # 4. Inizializza sistema protezione minori (se abilitato)
            try:
                from .simple_minor_protection import SimpleMinorProtection
                self.minor_protection = SimpleMinorProtection()
                
                # Carica configurazione e avvia se abilitato
                config = self.minor_protection.load_config()
                if config.get('enabled', False):
                    self.minor_protection.start_session()
                    self.logger.info("🛡️ Sistema protezione minori attivato")
                else:
                    self.logger.info("🛡️ Sistema protezione minori disponibile (disabilitato)")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Errore inizializzazione protezione minori: {e}")
                self.minor_protection = None
            
            # 5. Calcola tempo di avvio
            startup_duration = time.time() - self.startup_time
            self.logger.info(f"✅ P2P Core avviato in {startup_duration:.2f}s")
            
            self.is_running = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione core: {e}")
            return False
    
    def shutdown(self):
        """Chiude tutti i componenti del core"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 Chiusura P2P Core...")
        
        try:
            # Chiudi sistema protezione minori
            if self.minor_protection:
                try:
                    self.minor_protection.end_session()
                    self.logger.info("🛡️ Sessione protezione minori terminata")
                except Exception as e:
                    self.logger.warning(f"⚠️ Errore chiusura protezione minori: {e}")
            
            # Chiudi plugin
            if self.plugin_manager:
                for plugin_name in list(self.plugin_manager.loaded_plugins.keys()):
                    self.plugin_manager.unload_plugin(plugin_name)
                self.logger.info("🔌 Plugin chiusi")
            
            # Chiudi messaggistica
            if self.messaging:
                self.messaging.stop()
                self.logger.info("💬 Motore messaggistica fermato")
            
            self.is_running = False
            self.logger.info("✅ P2P Core chiuso correttamente")
            
        except Exception as e:
            self.logger.error(f"❌ Errore chiusura core: {e}")
    
    def send_message(self, recipient: str, content: str, message_type: str = "text") -> bool:
        """
        Invia messaggio a destinatario
        
        Args:
            recipient: Hash identità o nome destinatario
            content: Contenuto messaggio
            message_type: Tipo messaggio
            
        Returns:
            bool: True se invio riuscito
        """
        if not self.messaging:
            return False
        
        # Se recipient non è un hash, cerca per nome
        if len(recipient) != 64:  # Non è un hash
            peer = self.messaging.find_peer_by_name(recipient)
            if peer:
                recipient = peer.peer_hash
            else:
                self.logger.warning(f"Peer '{recipient}' non trovato")
                return False
        
        return self.messaging.send_message(recipient, content, message_type)
    
    def get_messages(self, peer: Optional[str] = None) -> List[Message]:
        """
        Ottiene messaggi dalla cronologia
        
        Args:
            peer: Hash o nome peer specifico
            
        Returns:
            List[Message]: Lista messaggi
        """
        if not self.messaging:
            return []
        
        peer_hash = None
        if peer:
            # Se peer non è un hash, cerca per nome
            if len(peer) != 64:
                peer_info = self.messaging.find_peer_by_name(peer)
                if peer_info:
                    peer_hash = peer_info.peer_hash
            else:
                peer_hash = peer
        
        return self.messaging.get_messages(peer_hash)
    
    def get_peers(self) -> List[PeerInfo]:
        """
        Ottiene lista peer conosciuti
        
        Returns:
            List[PeerInfo]: Lista peer
        """
        if not self.messaging:
            return []
        
        return self.messaging.get_peers()
    
    def get_identity(self) -> Optional[IdentityInfo]:
        """
        Ottiene identità corrente
        
        Returns:
            Optional[IdentityInfo]: Identità corrente
        """
        return self.identity_manager.get_current_identity()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Ottiene stato del core
        
        Returns:
            Dict[str, Any]: Informazioni stato
        """
        identity = self.get_identity()
        peers = self.get_peers()
        messages = self.get_messages()
        
        loaded_plugins = []
        if self.plugin_manager:
            loaded_plugins = list(self.plugin_manager.loaded_plugins.keys())
        
        uptime = 0
        if self.startup_time:
            uptime = time.time() - self.startup_time
        
        return {
            'running': self.is_running,
            'uptime': uptime,
            'identity': {
                'hash': identity.identity_hash[:16] + '...' if identity else None,
                'name': identity.display_name if identity else None
            },
            'network': {
                'peers_count': len(peers),
                'messages_count': len(messages)
            },
            'plugins': {
                'loaded_count': len(loaded_plugins),
                'loaded_names': loaded_plugins
            }
        }
    
    def _on_message_received(self, message: Message):
        """Callback messaggio ricevuto"""
        sender_name = "Sconosciuto"
        
        # Cerca nome mittente
        if self.messaging:
            for peer in self.messaging.get_peers():
                if peer.peer_hash == message.sender_hash:
                    sender_name = peer.display_name
                    break
        
        self.logger.info(f"📨 Messaggio da {sender_name}: {message.content[:50]}...")
        
        if self.message_received_callback:
            self.message_received_callback(message)
    
    def _on_peer_discovered(self, peer_info: PeerInfo):
        """Callback peer scoperto"""
        self.logger.info(f"👋 Nuovo peer: {peer_info.display_name} ({peer_info.peer_hash[:16]}...)")
        
        if self.peer_discovered_callback:
            self.peer_discovered_callback(peer_info)
    
    def _on_plugin_loaded(self, plugin_name: str, plugin_info):
        """Callback plugin caricato"""
        self.logger.info(f"🔌 Plugin caricato: {plugin_name} v{plugin_info.metadata.version}")
    
    def _on_plugin_error(self, plugin_name: str, error_message: str):
        """Callback errore plugin"""
        self.logger.error(f"🔌 Errore plugin {plugin_name}: {error_message}")


def create_app(config_path: Optional[str] = None, display_name: str = "P2P User") -> P2PCore:
    """
    Factory function per creare istanza P2P Core
    
    Args:
        config_path: Percorso configurazione
        display_name: Nome utente
        
    Returns:
        P2PCore: Istanza core inizializzata
    """
    core = P2PCore(config_path)
    
    if not core.initialize(display_name):
        raise RuntimeError("Impossibile inizializzare P2P Core")
    
    return core


def main():
    """Entry point principale per esecuzione standalone"""
    print("🌐 P2P Core Decentralizzato - Avvio Standalone")
    print("==============================================")
    
    # Gestione segnali per chiusura pulita
    core = None
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Ricevuto segnale {signum}, chiusura...")
        if core:
            core.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Crea e avvia core
        core = create_app()
        
        print(f"✅ P2P Core avviato correttamente!")
        print(f"👤 Identità: {core.get_identity().display_name}")
        print(f"🌐 Porta DHT: {core.messaging.dht.port}")
        print(f"🔌 Plugin caricati: {len(core.plugin_manager.loaded_plugins)}")
        print("\n💡 Premi Ctrl+C per uscire")
        
        # Loop principale
        while core.is_running:
            time.sleep(1)
            
            # Mostra stato ogni 30 secondi
            if int(time.time()) % 30 == 0:
                status = core.get_status()
                print(f"📊 Uptime: {status['uptime']:.0f}s | "
                      f"Peers: {status['network']['peers_count']} | "
                      f"Messaggi: {status['network']['messages_count']}")
    
    except KeyboardInterrupt:
        print("\n🛑 Interruzione utente")
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        if core:
            core.shutdown()
        print("👋 Arrivederci!")


# Export principali
__all__ = [
    'P2PCore',
    'P2PCoreAPI', 
    'create_app',
    'main',
    # Componenti core
    'LaboonCrypto',
    'IdentityManager',
    'LaboonMessaging',
    'LaboonPluginManager',
    'PluginInterface',
    # Strutture dati
    'IdentityInfo',
    'Message',
    'PeerInfo',
    # Configurazione esistente
    'Config',
    'Logger'
]


if __name__ == "__main__":
    main()