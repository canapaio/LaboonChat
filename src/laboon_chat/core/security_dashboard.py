"""
🔐 LaboonChat Security Dashboard
Dashboard per monitoraggio sicurezza plugin e sistema

Autore: Anima Digitale
Data: 2025-01-27
Versione: 1.0.0
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging


class SecurityLevel(Enum):
    """Livelli di sicurezza del sistema"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


class ThreatType(Enum):
    """Tipi di minacce rilevate"""
    MALICIOUS_PLUGIN = "malicious_plugin"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SIGNATURE_MISMATCH = "signature_mismatch"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    NETWORK_ANOMALY = "network_anomaly"
    RESOURCE_ABUSE = "resource_abuse"
    CERTIFICATION_DOWNGRADE = "certification_downgrade"


@dataclass
class SecurityEvent:
    """Evento di sicurezza"""
    timestamp: float
    event_type: ThreatType
    severity: SecurityLevel
    plugin_name: Optional[str]
    description: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None


@dataclass
class PluginSecurityStatus:
    """Status di sicurezza di un plugin"""
    name: str
    version: str
    certification_level: str
    trust_score: float
    last_verification: float
    active_threats: int
    quarantined: bool
    blocked: bool
    resource_usage: Dict[str, float]
    network_activity: Dict[str, int]


@dataclass
class SystemSecurityMetrics:
    """Metriche di sicurezza del sistema"""
    overall_security_level: SecurityLevel
    total_plugins: int
    certified_plugins: int
    quarantined_plugins: int
    blocked_plugins: int
    active_threats: int
    resolved_threats: int
    last_scan_time: float
    uptime: float
    boot_verification_status: str


class SecurityDashboard:
    """
    Dashboard principale per monitoraggio sicurezza
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("security_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Storage eventi e metriche
        self.events_file = self.data_dir / "security_events.json"
        self.metrics_file = self.data_dir / "security_metrics.json"
        self.plugins_file = self.data_dir / "plugin_status.json"
        self.cert_history_file = self.data_dir / "certification_history.json"
        
        # Cache in memoria
        self.security_events: List[SecurityEvent] = []
        self.plugin_statuses: Dict[str, PluginSecurityStatus] = {}
        self.system_metrics: Optional[SystemSecurityMetrics] = None
        self.certification_history: Dict[str, List[Dict]] = {}
        
        # Configurazione
        self.max_events = 1000
        self.event_retention_days = 30
        self.developer_mode = False  # Modalità sviluppatore
        
        # Carica dati esistenti
        self._load_data()
        
        self.logger.info("🔐 Security Dashboard inizializzata")
    
    def _load_data(self):
        """Carica dati persistenti"""
        try:
            # Carica eventi
            if self.events_file.exists():
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
                    self.security_events = [
                        SecurityEvent(**event) for event in events_data
                    ]
            
            # Carica status plugin
            if self.plugins_file.exists():
                with open(self.plugins_file, 'r', encoding='utf-8') as f:
                    plugins_data = json.load(f)
                    self.plugin_statuses = {
                        name: PluginSecurityStatus(**status)
                        for name, status in plugins_data.items()
                    }
            
            # Carica metriche sistema
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    metrics_data = json.load(f)
                    self.system_metrics = SystemSecurityMetrics(**metrics_data)
            
            # Carica cronologia certificazioni
            if self.cert_history_file.exists():
                with open(self.cert_history_file, 'r', encoding='utf-8') as f:
                    self.certification_history = json.load(f)
            
            self.logger.info(f"📊 Caricati {len(self.security_events)} eventi e {len(self.plugin_statuses)} plugin")
            
        except Exception as e:
            self.logger.error(f"❌ Errore caricamento dati: {e}")
    
    def _save_data(self):
        """Salva dati persistenti"""
        try:
            # Salva eventi (solo recenti)
            recent_events = self._get_recent_events()
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(event) for event in recent_events], f, indent=2)
            
            # Salva status plugin
            with open(self.plugins_file, 'w', encoding='utf-8') as f:
                json.dump({
                    name: asdict(status) 
                    for name, status in self.plugin_statuses.items()
                }, f, indent=2)
            
            # Salva metriche sistema
            if self.system_metrics:
                with open(self.metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.system_metrics), f, indent=2)
            
            # Salva cronologia certificazioni
            with open(self.cert_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.certification_history, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio dati: {e}")
    
    def _get_recent_events(self) -> List[SecurityEvent]:
        """Ottieni eventi recenti (ultimi 30 giorni)"""
        cutoff_time = time.time() - (self.event_retention_days * 24 * 3600)
        return [
            event for event in self.security_events 
            if event.timestamp > cutoff_time
        ][-self.max_events:]
    
    def log_security_event(self, 
                          event_type: ThreatType,
                          severity: SecurityLevel,
                          description: str,
                          plugin_name: Optional[str] = None,
                          details: Dict[str, Any] = None):
        """
        Registra un evento di sicurezza
        """
        event = SecurityEvent(
            timestamp=time.time(),
            event_type=event_type,
            severity=severity,
            plugin_name=plugin_name,
            description=description,
            details=details or {},
            resolved=False
        )
        
        self.security_events.append(event)
        
        # Log appropriato
        log_msg = f"🚨 {severity.value.upper()}: {description}"
        if plugin_name:
            log_msg += f" (Plugin: {plugin_name})"
        
        if severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]:
            self.logger.error(log_msg)
        elif severity == SecurityLevel.MEDIUM:
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
        
        # Salva immediatamente eventi critici
        if severity == SecurityLevel.CRITICAL:
            self._save_data()
    
    def update_plugin_status(self, plugin_status: PluginSecurityStatus):
        """Aggiorna status di sicurezza di un plugin"""
        plugin_name = plugin_status.name
        
        # Controlla downgrade certificazione
        if plugin_name in self.plugin_statuses:
            old_status = self.plugin_statuses[plugin_name]
            self._check_certification_downgrade(old_status, plugin_status)
        
        # Aggiorna cronologia certificazioni
        self._update_certification_history(plugin_status)
        
        # Aggiorna status corrente
        self.plugin_statuses[plugin_name] = plugin_status
        
        # Verifica se ci sono nuove minacce
        if plugin_status.active_threats > 0:
            self.log_security_event(
                ThreatType.SUSPICIOUS_BEHAVIOR,
                SecurityLevel.MEDIUM,
                f"Plugin {plugin_status.name} ha {plugin_status.active_threats} minacce attive",
                plugin_status.name,
                {"trust_score": plugin_status.trust_score}
            )
    
    def update_system_metrics(self, metrics: SystemSecurityMetrics):
        """Aggiorna metriche di sistema"""
        self.system_metrics = metrics
        
        # Verifica livello di sicurezza generale
        if metrics.overall_security_level in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]:
            self.log_security_event(
                ThreatType.NETWORK_ANOMALY,
                metrics.overall_security_level,
                f"Livello sicurezza sistema: {metrics.overall_security_level.value}",
                details=asdict(metrics)
            )
    
    def resolve_event(self, event_index: int, resolution_details: str = ""):
        """Risolvi un evento di sicurezza"""
        if 0 <= event_index < len(self.security_events):
            event = self.security_events[event_index]
            event.resolved = True
            event.resolution_time = time.time()
            
            if resolution_details:
                event.details["resolution"] = resolution_details
            
            self.logger.info(f"✅ Evento risolto: {event.description}")
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Ottieni riassunto sicurezza"""
        if not self.system_metrics:
            return {"error": "Metriche sistema non disponibili"}
        
        # Eventi recenti (ultime 24h)
        recent_cutoff = time.time() - (24 * 3600)
        recent_events = [
            event for event in self.security_events 
            if event.timestamp > recent_cutoff and not event.resolved
        ]
        
        # Plugin con problemi
        problematic_plugins = [
            status for status in self.plugin_statuses.values()
            if status.active_threats > 0 or status.quarantined or status.blocked
        ]
        
        return {
            "system_security_level": self.system_metrics.overall_security_level.value,
            "total_plugins": self.system_metrics.total_plugins,
            "certified_plugins": self.system_metrics.certified_plugins,
            "problematic_plugins": len(problematic_plugins),
            "recent_threats": len(recent_events),
            "uptime_hours": self.system_metrics.uptime / 3600,
            "last_scan": datetime.fromtimestamp(self.system_metrics.last_scan_time).isoformat(),
            "boot_verification": self.system_metrics.boot_verification_status
        }
    
    def get_plugin_report(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Ottieni report dettagliato di un plugin"""
        if plugin_name not in self.plugin_statuses:
            return None
        
        status = self.plugin_statuses[plugin_name]
        
        # Eventi correlati al plugin
        plugin_events = [
            event for event in self.security_events
            if event.plugin_name == plugin_name
        ]
        
        return {
            "name": status.name,
            "version": status.version,
            "certification_level": status.certification_level,
            "trust_score": status.trust_score,
            "status": {
                "quarantined": status.quarantined,
                "blocked": status.blocked,
                "active_threats": status.active_threats
            },
            "last_verification": datetime.fromtimestamp(status.last_verification).isoformat(),
            "resource_usage": status.resource_usage,
            "network_activity": status.network_activity,
            "security_events": len(plugin_events),
            "recent_events": [
                {
                    "type": event.event_type.value,
                    "severity": event.severity.value,
                    "description": event.description,
                    "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
                    "resolved": event.resolved
                }
                for event in plugin_events[-5:]  # Ultimi 5 eventi
            ]
        }
    
    def generate_security_report(self) -> str:
        """Genera report di sicurezza testuale"""
        if not self.system_metrics:
            return "❌ Metriche sistema non disponibili"
        
        report = []
        report.append("🔐 LABOON SECURITY DASHBOARD")
        report.append("=" * 50)
        report.append("")
        
        # Status generale
        report.append(f"🛡️ Livello Sicurezza: {self.system_metrics.overall_security_level.value.upper()}")
        report.append(f"⏱️ Uptime: {self.system_metrics.uptime/3600:.1f} ore")
        report.append(f"🔍 Ultima Scansione: {datetime.fromtimestamp(self.system_metrics.last_scan_time).strftime('%H:%M:%S')}")
        report.append(f"🚀 Boot Verification: {self.system_metrics.boot_verification_status}")
        report.append("")
        
        # Plugin
        report.append("📦 PLUGIN STATUS")
        report.append("-" * 20)
        report.append(f"Totali: {self.system_metrics.total_plugins}")
        report.append(f"Certificati: {self.system_metrics.certified_plugins}")
        report.append(f"In Quarantena: {self.system_metrics.quarantined_plugins}")
        report.append(f"Bloccati: {self.system_metrics.blocked_plugins}")
        report.append("")
        
        # Minacce
        active_threats = [e for e in self.security_events if not e.resolved]
        report.append("🚨 MINACCE ATTIVE")
        report.append("-" * 20)
        report.append(f"Totali: {len(active_threats)}")
        
        if active_threats:
            for threat in active_threats[-5:]:  # Ultime 5
                time_str = datetime.fromtimestamp(threat.timestamp).strftime('%H:%M')
                report.append(f"  {threat.severity.value.upper()} [{time_str}]: {threat.description}")
        else:
            report.append("  ✅ Nessuna minaccia attiva")
        
        report.append("")
        
        # Plugin problematici
        problematic = [p for p in self.plugin_statuses.values() if p.active_threats > 0]
        if problematic:
            report.append("⚠️ PLUGIN PROBLEMATICI")
            report.append("-" * 20)
            for plugin in problematic:
                report.append(f"  {plugin.name}: {plugin.active_threats} minacce (Trust: {plugin.trust_score:.2f})")
        
        return "\n".join(report)
    
    def _check_certification_downgrade(self, old_status: PluginSecurityStatus, new_status: PluginSecurityStatus):
        """Controlla se c'è stato un downgrade di certificazione"""
        cert_levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
        
        old_level = cert_levels.get(old_status.certification_level, 0)
        new_level = cert_levels.get(new_status.certification_level, 0)
        
        if new_level < old_level:
            # DOWNGRADE RILEVATO!
            self._handle_certification_downgrade(old_status, new_status)
    
    def _handle_certification_downgrade(self, old_status: PluginSecurityStatus, new_status: PluginSecurityStatus):
        """Gestisce il downgrade di certificazione con avvertimento"""
        plugin_name = new_status.name
        
        # Se in modalità sviluppatore, log semplice senza avvertimento
        if self.developer_mode:
            self.logger.info(f"🛠️ MODALITÀ DEV: Downgrade certificazione {plugin_name} da {old_status.certification_level} a {new_status.certification_level} - IGNORATO")
            return
        
        # Log evento critico
        self.log_security_event(
            ThreatType.CERTIFICATION_DOWNGRADE,
            SecurityLevel.HIGH,
            f"🚨 DOWNGRADE CERTIFICAZIONE: {plugin_name} da {old_status.certification_level} a {new_status.certification_level}",
            plugin_name,
            {
                "old_certification": old_status.certification_level,
                "new_certification": new_status.certification_level,
                "old_trust_score": old_status.trust_score,
                "new_trust_score": new_status.trust_score
            }
        )
        
        # Mostra avvertimento interattivo
        self._show_downgrade_warning(plugin_name, old_status.certification_level, new_status.certification_level)
    
    def _show_downgrade_warning(self, plugin_name: str, old_cert: str, new_cert: str):
        """Mostra avvertimento interattivo per downgrade"""
        print("\n" + "="*60)
        print("🚨 AVVERTIMENTO SICUREZZA - DOWNGRADE CERTIFICAZIONE")
        print("="*60)
        print(f"Plugin: {plugin_name}")
        print(f"Certificazione precedente: {old_cert}")
        print(f"Certificazione attuale: {new_cert}")
        print("\n⚠️  QUESTO POTREBBE INDICARE:")
        print("   • Plugin compromesso o modificato")
        print("   • Certificazione scaduta o revocata")
        print("   • Possibile minaccia alla sicurezza")
        print("\n🔧 OPZIONI:")
        print("   1. Bloccare il plugin (RACCOMANDATO)")
        print("   2. Mettere in quarantena")
        print("   3. Ignorare (solo se sei uno sviluppatore)")
        print("="*60)
        
        try:
            choice = input("\nScegli un'opzione (1/2/3): ").strip()
            
            if choice == "1":
                # Blocca plugin
                self.logger.warning(f"🚫 Plugin {plugin_name} BLOCCATO per downgrade certificazione")
                return "BLOCK"
            elif choice == "2":
                # Quarantena
                self.logger.warning(f"🔒 Plugin {plugin_name} in QUARANTENA per downgrade certificazione")
                return "QUARANTINE"
            elif choice == "3":
                # Chiedi se è sviluppatore
                dev_confirm = input("\n🔧 Sei uno sviluppatore che sta lavorando su questo plugin? (s/n): ").strip().lower()
                if dev_confirm in ['s', 'si', 'y', 'yes']:
                    enable_dev_mode = input("🛠️  Vuoi abilitare la modalità sviluppatore per questa sessione? (s/n): ").strip().lower()
                    if enable_dev_mode in ['s', 'si', 'y', 'yes']:
                        self.developer_mode = True
                        self.logger.info("🛠️ Modalità sviluppatore ABILITATA per questa sessione")
                        print("✅ Modalità sviluppatore attivata - avvertimenti downgrade disabilitati")
                    return "ALLOW"
                else:
                    self.logger.warning(f"🚫 Plugin {plugin_name} BLOCCATO - accesso negato")
                    return "BLOCK"
            else:
                # Default: blocca
                self.logger.warning(f"🚫 Plugin {plugin_name} BLOCCATO - scelta non valida")
                return "BLOCK"
                
        except (KeyboardInterrupt, EOFError):
            self.logger.warning(f"🚫 Plugin {plugin_name} BLOCCATO - input interrotto")
            return "BLOCK"
    
    def _update_certification_history(self, plugin_status: PluginSecurityStatus):
        """Aggiorna cronologia certificazioni"""
        plugin_name = plugin_status.name
        
        if plugin_name not in self.certification_history:
            self.certification_history[plugin_name] = []
        
        # Aggiungi entry cronologia
        history_entry = {
            "timestamp": time.time(),
            "certification_level": plugin_status.certification_level,
            "trust_score": plugin_status.trust_score,
            "version": plugin_status.version
        }
        
        self.certification_history[plugin_name].append(history_entry)
        
        # Mantieni solo ultimi 50 record per plugin
        if len(self.certification_history[plugin_name]) > 50:
            self.certification_history[plugin_name] = self.certification_history[plugin_name][-50:]
    
    def set_developer_mode(self, enabled: bool):
        """Abilita/disabilita modalità sviluppatore"""
        self.developer_mode = enabled
        mode_str = "ABILITATA" if enabled else "DISABILITATA"
        self.logger.info(f"🛠️ Modalità sviluppatore {mode_str}")
    
    def get_certification_history(self, plugin_name: str) -> List[Dict]:
        """Ottieni cronologia certificazioni di un plugin"""
        return self.certification_history.get(plugin_name, [])
    
    def cleanup_old_data(self):
        """Pulisci dati vecchi"""
        # Rimuovi eventi vecchi
        cutoff_time = time.time() - (self.event_retention_days * 24 * 3600)
        old_count = len(self.security_events)
        self.security_events = [
            event for event in self.security_events 
            if event.timestamp > cutoff_time
        ]
        
        removed = old_count - len(self.security_events)
        if removed > 0:
            self.logger.info(f"🧹 Rimossi {removed} eventi vecchi")
            self._save_data()
    
    def shutdown(self):
        """Chiudi dashboard e salva dati"""
        self.logger.info("🛑 Chiusura Security Dashboard...")
        self._save_data()
        self.cleanup_old_data()


# Funzione di utilità per integrazione
def create_security_dashboard(data_dir: Path = None) -> SecurityDashboard:
    """Crea e inizializza dashboard sicurezza"""
    return SecurityDashboard(data_dir)


# Test e demo
if __name__ == "__main__":
    import asyncio
    
    async def test_certification_downgrade():
        """Test sistema avvertimento downgrade"""
        print("🧪 Test Sistema Avvertimento Downgrade Certificazione")
        print("="*60)
        
        # Crea dashboard
        dashboard = create_security_dashboard(Path("test_security_data"))
        
        # Simula plugin con certificazione alta
        old_status = PluginSecurityStatus(
            name="test_plugin",
            version="1.0.0",
            certification_level="HIGH",
            trust_score=95.0,
            last_verification=time.time(),
            active_threats=0,
            quarantined=False,
            blocked=False,
            resource_usage={"cpu": 2.0, "memory": 64.0},
            network_activity={"connections": 1, "bytes_sent": 512}
        )
        
        # Aggiorna con status iniziale
        dashboard.update_plugin_status(old_status)
        print(f"✅ Plugin inizializzato con certificazione {old_status.certification_level}")
        
        # Simula downgrade a certificazione bassa
        new_status = PluginSecurityStatus(
            name="test_plugin",
            version="1.0.1",
            certification_level="LOW",
            trust_score=45.0,
            last_verification=time.time(),
            active_threats=1,
            quarantined=False,
            blocked=False,
            resource_usage={"cpu": 5.0, "memory": 128.0},
            network_activity={"connections": 3, "bytes_sent": 2048}
        )
        
        print(f"\n🚨 Simulando downgrade a certificazione {new_status.certification_level}...")
        
        # Questo dovrebbe triggerare l'avvertimento
        dashboard.update_plugin_status(new_status)
        
        # Mostra report finale
        print("\n📊 REPORT FINALE:")
        print(dashboard.generate_security_report())
        
        # Test modalità sviluppatore
        print("\n🛠️ Test modalità sviluppatore...")
        dashboard.set_developer_mode(True)
        
        # Nuovo downgrade - non dovrebbe mostrare avvertimento
        newer_status = PluginSecurityStatus(
            name="test_plugin",
            version="1.0.2",
            certification_level="NONE",
            trust_score=20.0,
            last_verification=time.time(),
            active_threats=2,
            quarantined=True,
            blocked=False,
            resource_usage={"cpu": 10.0, "memory": 256.0},
            network_activity={"connections": 5, "bytes_sent": 4096}
        )
        
        print(f"🔄 Downgrade ulteriore a {newer_status.certification_level} (modalità dev attiva)")
        dashboard.update_plugin_status(newer_status)
        
        print("\n✅ Test completato!")
    
    # Esegui test
    asyncio.run(test_certification_downgrade())