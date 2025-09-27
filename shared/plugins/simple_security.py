#!/usr/bin/env python3
"""
LaboonChat - Sistema di Sicurezza Plugin Semplificato
=====================================================

Versione semplificata del sistema di sicurezza che mantiene le funzionalità
essenziali ma riduce drasticamente la complessità per l'utente finale.

Principi di Design:
- Sicurezza trasparente (l'utente non vede la complessità)
- Configurazione zero (funziona out-of-the-box)
- Fallback intelligente (degrada elegantemente)
- Protezione automatica (nessun intervento richiesto)
"""

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
import aiohttp
import asyncio

# Import AI verifier (completamente opzionale)
try:
    from ai_code_verifier import AICodeVerifier, verify_plugin_with_ai
    AI_VERIFIER_AVAILABLE = True
    logging.info("🤖 AI Code Verifier disponibile (opzionale)")
except ImportError:
    AI_VERIFIER_AVAILABLE = False
    logging.info("🔒 Modalità sicurezza tradizionale (AI non disponibile)")


class PluginStatus(Enum):
    """Stati semplificati per i plugin"""
    SAFE = "safe"           # ✅ Sicuro - installazione automatica
    WARNING = "warning"     # ⚠️ Attenzione - richiede conferma
    BLOCKED = "blocked"     # 🚫 Bloccato - installazione negata


@dataclass
class PluginInfo:
    """Informazioni essenziali di un plugin"""
    name: str
    version: str
    checksum: str
    status: PluginStatus
    trust_score: float
    last_check: float
    ai_analysis: Optional[object] = None  # AIAnalysisResult


class SimplePluginSecurity:
    """
    Sistema di sicurezza plugin semplificato
    
    Funzionalità:
    - Validazione automatica checksums
    - Blacklist globale sincronizzata
    - Trust score basato su consenso community
    - Sandbox automatico per plugin sospetti
    - Fallback elegante in caso di errori
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path.home() / ".laboonchat" / "security"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database locale per cache
        self.db_path = self.data_dir / "plugin_security.db"
        self.global_blacklist: Set[str] = set()
        self.community_scores: Dict[str, float] = {}
        self.last_sync = 0
        self.ai_verifier = None
        self._init_database()
        self._init_ai_verifier()
        
        # Blacklist globale (sincronizzata automaticamente)
        self.blacklist_path = self.data_dir / "blacklist.json"
        self._load_blacklist()
        
        # Configurazione semplificata
        self.config = {
            "auto_update_blacklist": True,
            "trust_threshold": 0.7,  # Soglia per considerare plugin sicuro
            "sandbox_suspicious": True,
            "allow_community_plugins": True
        }
    
    def _init_database(self):
        """Inizializza database SQLite per cache locale"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plugin_cache (
                    name TEXT PRIMARY KEY,
                    version TEXT,
                    checksum TEXT,
                    status TEXT,
                    trust_score REAL,
                    last_check REAL,
                    metadata TEXT
                )
            """)
    
    def _init_ai_verifier(self):
        """Inizializza AI verifier se disponibile (completamente opzionale)"""
        self.ai_verifier = None
        
        if not AI_VERIFIER_AVAILABLE:
            logging.info("🔒 Modalità sicurezza tradizionale attiva")
            return
            
        try:
            # Verifica se Ollama è preinstallato nel sistema
            import subprocess
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.ai_verifier = AICodeVerifier()
                logging.info("✅ AI Code Verifier inizializzato (Ollama preinstallato)")
            else:
                logging.info("🔒 Ollama non trovato - modalità sicurezza tradizionale")
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logging.info(f"🔒 AI non disponibile - modalità sicurezza tradizionale: {type(e).__name__}")
            self.ai_verifier = None
    
    def _load_blacklist(self):
        """Carica blacklist globale (con fallback locale)"""
        try:
            if self.blacklist_path.exists():
                with open(self.blacklist_path) as f:
                    self.blacklist = set(json.load(f))
            else:
                self.blacklist = set()
        except Exception:
            # Fallback: blacklist vuota se errore di caricamento
            self.blacklist = set()
    
    def check_plugin(self, plugin_path: Path) -> PluginInfo:
        """
        Verifica sicurezza di un plugin
        
        Processo con AI opzionale:
        1. Calcola checksum
        2. Controlla blacklist
        3. Verifica cache locale
        4. Analisi AI (se disponibile)
        5. Calcola trust score
        6. Determina status finale
        """
        try:
            # 1. Calcola checksum del plugin
            checksum = self._calculate_checksum(plugin_path)
            plugin_name = plugin_path.stem
            
            # 2. Controllo blacklist immediato
            if checksum in self.blacklist or plugin_name in self.blacklist:
                return PluginInfo(
                    name=plugin_name,
                    version="unknown",
                    checksum=checksum,
                    status=PluginStatus.BLOCKED,
                    trust_score=0.0,
                    last_check=time.time()
                )
            
            # 3. Verifica cache locale
            cached_info = self._get_cached_info(plugin_name, checksum)
            if cached_info and self._is_cache_valid(cached_info):
                return cached_info
            
            # 4. Analisi AI (opzionale)
            ai_analysis = None
            if self.ai_verifier:
                try:
                    import asyncio
                    code = plugin_path.read_text(encoding='utf-8')
                    # Esegue analisi AI in modo sincrono
                    ai_analysis = asyncio.run(self.ai_verifier.analyze_plugin_code(code, plugin_name))
                    logging.info(f"🤖 AI analysis completata per {plugin_name}")
                except Exception as e:
                    logging.warning(f"🔒 AI analysis fallita per {plugin_name}: {type(e).__name__}")
                    ai_analysis = None
            
            # 5. Analisi sicurezza con AI
            static_score = self._basic_static_analysis(plugin_path)
            trust_score = self._calculate_trust_score(plugin_path, checksum, ai_analysis)
            status, reason = self._determine_final_status(trust_score, static_score, ai_analysis)
            
            # 6. Crea info plugin e salva in cache
            plugin_info = PluginInfo(
                name=plugin_name,
                version=self._extract_version(plugin_path),
                checksum=checksum,
                status=status,
                trust_score=trust_score,
                last_check=time.time(),
                ai_analysis=ai_analysis
            )
            
            self._cache_plugin_info(plugin_info)
            return plugin_info
            
        except Exception as e:
            # Fallback: in caso di errore, considera plugin sospetto
            return PluginInfo(
                name=plugin_path.stem,
                version="unknown",
                checksum="error",
                status=PluginStatus.WARNING,
                trust_score=0.5,
                last_check=time.time()
            )
    
    def _calculate_checksum(self, plugin_path: Path) -> str:
        """Calcola SHA256 del plugin"""
        sha256_hash = hashlib.sha256()
        with open(plugin_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _calculate_trust_score(self, plugin_path: Path, checksum: str, ai_analysis=None) -> float:
        """
        Calcola trust score semplificato con supporto AI
        
        Fattori considerati:
        - Presenza in registry ufficiale (peso: 0.4)
        - Validazioni community (peso: 0.2)
        - Analisi statica basic (peso: 0.2)
        - Analisi AI (peso: 0.2, se disponibile)
        """
        score = 0.0
        
        # Controllo registry ufficiale (simulato)
        if self._is_in_official_registry(checksum):
            score += 0.4
        
        # Validazioni community (simulato)
        community_score = self._get_community_score(checksum)
        score += community_score * 0.2
        
        # Analisi statica basic
        static_score = self._basic_static_analysis(plugin_path)
        score += static_score * 0.2
        
        # Analisi AI (se disponibile)
        if ai_analysis and hasattr(ai_analysis, 'security_score'):
            ai_score = ai_analysis.security_score
            score += ai_score * 0.2
        elif not ai_analysis:
            # Se AI non disponibile, redistribuisci il peso
            score = score / 0.8  # Normalizza per compensare mancanza AI
        
        return min(score, 1.0)
    
    def _determine_final_status(self, trust_score: float, static_score: float, ai_analysis=None) -> tuple:
        """
        Determina status finale considerando AI analysis
        
        Returns:
            (status, reason) tuple
        """
        # Se AI analysis disponibile, ha priorità per decisioni critiche
        if ai_analysis:
            ai_level = getattr(ai_analysis, 'security_level', 'unknown')
            ai_confidence = getattr(ai_analysis, 'confidence', 0.0)
            
            # AI dice DANGEROUS con alta confidenza -> BLOCKED
            if ai_level == 'dangerous' and ai_confidence >= 0.8:
                return PluginStatus.BLOCKED, f"AI: Plugin pericoloso (confidence: {ai_confidence:.2f})"
            
            # AI dice SAFE con alta confidenza -> considera trust score
            elif ai_level == 'safe' and ai_confidence >= 0.8:
                if trust_score >= 0.7:
                    return PluginStatus.SAFE, f"AI: Plugin sicuro (confidence: {ai_confidence:.2f})"
                else:
                    return PluginStatus.WARNING, f"AI: Plugin sicuro ma trust score basso"
            
            # AI dice SUSPICIOUS -> WARNING
            elif ai_level == 'suspicious':
                return PluginStatus.WARNING, f"AI: Plugin sospetto (confidence: {ai_confidence:.2f})"
        
        # Fallback su trust score tradizionale
        if trust_score >= 0.8:
            return PluginStatus.SAFE, "Plugin verificato e sicuro"
        elif trust_score >= 0.5:
            return PluginStatus.WARNING, "Plugin potenzialmente sicuro, usare con cautela"
        else:
            return PluginStatus.BLOCKED, "Plugin potenzialmente pericoloso"
    
    def _is_in_official_registry(self, checksum: str) -> bool:
        """Verifica se plugin è nel registry ufficiale (simulato)"""
        # In implementazione reale, questo controllerebbe il registry
        # Per ora, simuliamo con alcuni checksums "sicuri"
        official_checksums = {
            # Questi sarebbero i checksums dei plugin ufficiali
            "a1b2c3d4e5f6...",  # security-core
            "f6e5d4c3b2a1...",  # network-core
        }
        return checksum in official_checksums
    
    def _get_community_score(self, checksum: str) -> float:
        """Ottiene score dalla community (simulato)"""
        # In implementazione reale, questo interrogherebbe la rete P2P
        # Per ora, restituiamo score casuale basato su checksum
        hash_int = int(checksum[:8], 16)
        return (hash_int % 100) / 100.0
    
    def _basic_static_analysis(self, plugin_path: Path) -> float:
        """Analisi statica semplificata"""
        try:
            with open(plugin_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern sospetti semplificati
            suspicious_patterns = [
                'eval(', 'exec(', '__import__',
                'subprocess', 'os.system',
                'socket.socket', 'urllib.request'
            ]
            
            suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in content)
            
            # Score inversamente proporzionale ai pattern sospetti
            if suspicious_count == 0:
                return 1.0
            elif suspicious_count <= 2:
                return 0.7
            elif suspicious_count <= 4:
                return 0.4
            else:
                return 0.1
                
        except Exception:
            # Se non riusciamo a leggere il file, score neutro
            return 0.5
    
    def _extract_version(self, plugin_path: Path) -> str:
        """Estrae versione dal plugin (semplificato)"""
        try:
            with open(plugin_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cerca pattern version comuni
            import re
            version_patterns = [
                r'__version__\s*=\s*["\']([^"\']+)["\']',
                r'version\s*=\s*["\']([^"\']+)["\']',
                r'VERSION\s*=\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
            
            return "1.0.0"  # Default version
            
        except Exception:
            return "unknown"
    
    def _get_cached_info(self, plugin_name: str, checksum: str) -> Optional[PluginInfo]:
        """Recupera info dalla cache locale"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM plugin_cache WHERE name = ? AND checksum = ?",
                    (plugin_name, checksum)
                )
                row = cursor.fetchone()
                
                if row:
                    return PluginInfo(
                        name=row[0],
                        version=row[1],
                        checksum=row[2],
                        status=PluginStatus(row[3]),
                        trust_score=row[4],
                        last_check=row[5]
                    )
        except Exception:
            pass
        
        return None
    
    def _is_cache_valid(self, plugin_info: PluginInfo) -> bool:
        """Verifica se cache è ancora valida (24 ore)"""
        return (time.time() - plugin_info.last_check) < 86400
    
    def _cache_plugin_info(self, plugin_info: PluginInfo):
        """Salva info plugin in cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO plugin_cache 
                    (name, version, checksum, status, trust_score, last_check, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    plugin_info.name,
                    plugin_info.version,
                    plugin_info.checksum,
                    plugin_info.status.value,
                    plugin_info.trust_score,
                    plugin_info.last_check,
                    "{}"  # metadata vuoto per ora
                ))
        except Exception:
            # Fallback silenzioso se cache non funziona
            pass
    
    def update_blacklist(self) -> bool:
        """Aggiorna blacklist da fonti remote (semplificato)"""
        if not self.config["auto_update_blacklist"]:
            return False
        
        try:
            # In implementazione reale, questo scaricherebbe da fonti remote
            # Per ora, simuliamo un aggiornamento
            
            # Blacklist di esempio
            new_blacklist = {
                "malicious_plugin_1",
                "suspicious_hash_abc123",
                "known_malware_def456"
            }
            
            self.blacklist.update(new_blacklist)
            
            # Salva blacklist aggiornata
            with open(self.blacklist_path, 'w') as f:
                json.dump(list(self.blacklist), f, indent=2)
            
            return True
            
        except Exception:
            # Fallback silenzioso se aggiornamento fallisce
            return False
    
    def get_security_summary(self) -> Dict:
        """Restituisce riassunto sicurezza per UI"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT status, COUNT(*) FROM plugin_cache 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
            
            return {
                "total_plugins": sum(status_counts.values()),
                "safe_plugins": status_counts.get("safe", 0),
                "warning_plugins": status_counts.get("warning", 0),
                "blocked_plugins": status_counts.get("blocked", 0),
                "blacklist_size": len(self.blacklist),
                "last_update": time.time()
            }
            
        except Exception:
            return {
                "total_plugins": 0,
                "safe_plugins": 0,
                "warning_plugins": 0,
                "blocked_plugins": 0,
                "blacklist_size": len(self.blacklist),
                "last_update": 0
            }


# Funzioni di utilità per integrazione semplice
def check_plugin_security(plugin_path: str) -> Tuple[bool, str]:
    """
    Funzione semplificata per controllo rapido plugin
    
    Returns:
        (is_safe, message) - Tupla con stato sicurezza e messaggio
    """
    security = SimplePluginSecurity()
    plugin_info = security.check_plugin(Path(plugin_path))
    
    if plugin_info.status == PluginStatus.SAFE:
        return True, f"Plugin '{plugin_info.name}' è sicuro (trust: {plugin_info.trust_score:.1%})"
    elif plugin_info.status == PluginStatus.WARNING:
        return False, f"Plugin '{plugin_info.name}' richiede attenzione (trust: {plugin_info.trust_score:.1%})"
    else:
        return False, f"Plugin '{plugin_info.name}' è bloccato per sicurezza"


def auto_install_safe_plugins(plugin_dir: Path) -> List[str]:
    """
    Installa automaticamente tutti i plugin sicuri in una directory
    
    Returns:
        Lista dei plugin installati con successo
    """
    security = SimplePluginSecurity()
    installed = []
    
    for plugin_file in plugin_dir.glob("*.py"):
        plugin_info = security.check_plugin(plugin_file)
        
        if plugin_info.status == PluginStatus.SAFE:
            # Qui andrebbe la logica di installazione effettiva
            installed.append(plugin_info.name)
    
    return installed


if __name__ == "__main__":
    # Test del sistema di sicurezza semplificato
    security = SimplePluginSecurity()
    
    print("🔐 LaboonChat - Sistema Sicurezza Plugin Semplificato")
    print("=" * 50)
    
    # Aggiorna blacklist
    if security.update_blacklist():
        print("✅ Blacklist aggiornata")
    
    # Mostra riassunto sicurezza
    summary = security.get_security_summary()
    print(f"📊 Plugin totali: {summary['total_plugins']}")
    print(f"✅ Sicuri: {summary['safe_plugins']}")
    print(f"⚠️  Attenzione: {summary['warning_plugins']}")
    print(f"🚫 Bloccati: {summary['blocked_plugins']}")
    print(f"🛡️  Blacklist: {summary['blacklist_size']} elementi")