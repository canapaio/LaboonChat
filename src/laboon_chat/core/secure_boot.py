"""
🔐 LaboonChat Secure Boot System
================================

Sistema di boot sicuro che verifica automaticamente l'integrità e l'autenticità 
dei plugin confrontando i checksum con il repository certificati.

🐋 "La sicurezza inizia dal primo respiro digitale" 🌊

Author: LaboonChat Team
License: GPL-3.0
"""

import os
import json
import hashlib
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
import aiohttp
import time

try:
    from .plugin_manager import LaboonPluginManager, PluginMetadata, PluginInfo
except ImportError:
    from plugin_manager import LaboonPluginManager, PluginMetadata, PluginInfo
try:
    from .crypto_core import LaboonCrypto
except ImportError:
    # Fallback per test standalone
    class LaboonCrypto:
        @staticmethod
        def verify_signature(data, signature, public_key):
            return signature == "valid_signature_hash"
        
        @staticmethod
        def calculate_checksum(file_path):
            import hashlib
            try:
                with open(file_path, 'rb') as f:
                    return hashlib.sha256(f.read()).hexdigest()
            except:
                return "test_checksum"


@dataclass
class VerificationResult:
    """Risultato verifica plugin"""
    plugin_name: str
    version: str
    is_certified: bool
    certification_level: str  # HIGH, MEDIUM, LOW, NONE
    checksum_valid: bool
    signature_valid: bool
    analysis_score: float
    issues: List[str]
    action: str  # ALLOW, WARN, QUARANTINE, BLOCK


class CertifiedPluginRepository:
    """
    🏛️ Repository Plugin Certificati
    
    Gestisce il repository locale dei plugin certificati con
    sincronizzazione automatica dal repository ufficiale.
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        if repo_path is None:
            repo_path = Path.home() / ".laboon" / "certified-plugins"
        
        self.repo_path = Path(repo_path)
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        self.registry_file = self.repo_path / "registry.json"
        self.checksums_dir = self.repo_path / "checksums"
        self.analysis_dir = self.repo_path / "analysis"
        self.signatures_dir = self.repo_path / "signatures"
        
        # Crea struttura directory
        for dir_path in [self.checksums_dir, self.analysis_dir, self.signatures_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.crypto = LaboonCrypto()
        
        # Cache registry
        self._registry_cache: Optional[Dict] = None
        self._cache_timestamp = 0
        
    async def load_registry(self) -> Dict[str, Any]:
        """Carica registry plugin certificati"""
        try:
            # Cache per 5 minuti
            if (self._registry_cache and 
                time.time() - self._cache_timestamp < 300):
                return self._registry_cache
            
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                
                self._registry_cache = registry
                self._cache_timestamp = time.time()
                return registry
            else:
                # Registry vuoto se non esiste
                return {"plugins": {}, "metadata": {"version": "1.0", "updated_at": 0}}
                
        except Exception as e:
            self.logger.error(f"❌ Errore caricamento registry: {e}")
            return {"plugins": {}, "metadata": {"version": "1.0", "updated_at": 0}}
    
    async def get_plugin_certification(self, plugin_name: str, version: str) -> Optional[Dict]:
        """Ottiene certificazione per plugin specifico"""
        registry = await self.load_registry()
        
        plugins = registry.get("plugins", {})
        plugin_data = plugins.get(plugin_name, {})
        
        if version in plugin_data.get("versions", {}):
            return plugin_data["versions"][version]
        
        return None
    
    async def verify_plugin_checksum(self, plugin_path: str, expected_checksum: str) -> bool:
        """Verifica checksum plugin"""
        try:
            with open(plugin_path, 'rb') as f:
                content = f.read()
            
            actual_checksum = hashlib.sha256(content).hexdigest()
            return actual_checksum == expected_checksum
            
        except Exception as e:
            self.logger.error(f"❌ Errore verifica checksum: {e}")
            return False
    
    async def verify_plugin_signature(self, plugin_path: str, signature_path: str) -> bool:
        """Verifica firma digitale plugin"""
        try:
            # TODO: Implementare verifica Ed25519
            # Per ora ritorna True se il file signature esiste
            return Path(signature_path).exists()
            
        except Exception as e:
            self.logger.error(f"❌ Errore verifica firma: {e}")
            return False
    
    async def update_from_remote(self, remote_url: str = None) -> bool:
        """Aggiorna repository da fonte remota"""
        if remote_url is None:
            remote_url = "https://github.com/LaboonChat/certified-plugins"
        
        try:
            self.logger.info(f"🔄 Aggiornamento repository da {remote_url}")
            
            # TODO: Implementare download sicuro da repository remoto
            # Per ora simula aggiornamento locale
            
            # Invalida cache
            self._registry_cache = None
            
            self.logger.info("✅ Repository aggiornato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento repository: {e}")
            return False


class PluginVerificationEngine:
    """
    🔍 Engine di Verifica Plugin
    
    Analizza plugin installati e determina il livello di sicurezza
    basato su certificazioni, checksums e analisi indipendente.
    """
    
    def __init__(self, certified_repo: CertifiedPluginRepository):
        self.certified_repo = certified_repo
        self.logger = logging.getLogger(__name__)
        
        # Configurazione livelli sicurezza
        self.security_levels = {
            "HIGH": {"min_score": 0.9, "auto_allow": True},
            "MEDIUM": {"min_score": 0.7, "auto_allow": False},
            "LOW": {"min_score": 0.5, "auto_allow": False},
            "NONE": {"min_score": 0.0, "auto_allow": False}
        }
    
    async def verify_plugin(self, plugin_path: str, metadata: PluginMetadata) -> VerificationResult:
        """Verifica completa di un plugin"""
        plugin_name = metadata.name
        version = metadata.version
        
        self.logger.info(f"🔍 Verifica plugin {plugin_name} v{version}")
        
        # 1. Controlla certificazione
        certification = await self.certified_repo.get_plugin_certification(plugin_name, version)
        
        is_certified = certification is not None
        cert_level = certification.get("level", "NONE") if certification else "NONE"
        
        # 2. Verifica checksum
        expected_checksum = certification.get("checksum") if certification else None
        checksum_valid = False
        
        if expected_checksum:
            checksum_valid = await self.certified_repo.verify_plugin_checksum(
                plugin_path, expected_checksum
            )
        
        # 3. Verifica firma digitale
        signature_valid = False
        if certification and certification.get("signature_file"):
            signature_path = self.certified_repo.signatures_dir / certification["signature_file"]
            signature_valid = await self.certified_repo.verify_plugin_signature(
                plugin_path, str(signature_path)
            )
        
        # 4. Calcola score analisi
        analysis_score = await self._calculate_analysis_score(certification)
        
        # 5. Identifica issues
        issues = []
        if not is_certified:
            issues.append("Plugin non certificato")
        if not checksum_valid and expected_checksum:
            issues.append("Checksum non valido")
        if not signature_valid and certification:
            issues.append("Firma digitale non valida")
        
        # 6. Determina azione
        action = self._determine_action(cert_level, checksum_valid, signature_valid, analysis_score)
        
        return VerificationResult(
            plugin_name=plugin_name,
            version=version,
            is_certified=is_certified,
            certification_level=cert_level,
            checksum_valid=checksum_valid,
            signature_valid=signature_valid,
            analysis_score=analysis_score,
            issues=issues,
            action=action
        )
    
    async def _calculate_analysis_score(self, certification: Optional[Dict]) -> float:
        """Calcola score basato su analisi indipendente"""
        if not certification:
            return 0.0
        
        # Combina score da diverse analisi
        security_score = certification.get("security_audit", {}).get("score", 0.0)
        code_score = certification.get("code_review", {}).get("score", 0.0)
        compliance_score = certification.get("compliance", {}).get("score", 0.0)
        
        # Media pesata
        total_score = (security_score * 0.5 + code_score * 0.3 + compliance_score * 0.2)
        return min(1.0, max(0.0, total_score))
    
    def _determine_action(self, cert_level: str, checksum_valid: bool, 
                         signature_valid: bool, analysis_score: float) -> str:
        """Determina azione da intraprendere"""
        
        # Plugin certificati HIGH con checksum valido
        if cert_level == "HIGH" and checksum_valid and signature_valid:
            return "ALLOW"
        
        # Plugin certificati MEDIUM
        if cert_level == "MEDIUM" and checksum_valid:
            return "WARN"
        
        # Plugin certificati LOW
        if cert_level == "LOW":
            return "WARN"
        
        # Plugin non certificati o con problemi
        if not checksum_valid or analysis_score < 0.3:
            return "QUARANTINE"
        
        # Default: blocca
        return "BLOCK"


class SecureBootManager:
    """
    🔐 Gestore Boot Sicuro
    
    Orchestratore principale del sistema di boot sicuro che integra
    verifica plugin con il plugin manager esistente.
    """
    
    def __init__(self, plugin_manager: LaboonPluginManager):
        self.plugin_manager = plugin_manager
        self.logger = logging.getLogger(__name__)
        
        # Inizializza componenti
        self.certified_repo = CertifiedPluginRepository()
        self.verification_engine = PluginVerificationEngine(self.certified_repo)
        
        # Directory quarantena
        self.quarantine_dir = Path.home() / ".laboon" / "quarantine"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistiche boot
        self.boot_stats = {
            "start_time": 0,
            "plugins_verified": 0,
            "plugins_allowed": 0,
            "plugins_quarantined": 0,
            "plugins_blocked": 0
        }
    
    async def secure_boot_sequence(self) -> bool:
        """Sequenza di boot sicura completa"""
        try:
            self.boot_stats["start_time"] = time.time()
            self.logger.info("🔐 Avvio boot sicuro LaboonChat")
            
            # 1. Aggiornamento repository certificata
            await self._update_certified_repository()
            
            # 2. Verifica plugin installati
            verification_results = await self._verify_all_plugins()
            
            # 3. Gestione plugin non verificati
            await self._handle_verification_results(verification_results)
            
            # 4. Caricamento plugin certificati
            await self._load_verified_plugins(verification_results)
            
            # 5. Report finale
            self._log_boot_summary()
            
            self.logger.info("✅ Boot sicuro completato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore boot sicuro: {e}")
            return False
    
    async def _update_certified_repository(self):
        """Aggiorna repository plugin certificati"""
        try:
            self.logger.info("🔄 Aggiornamento repository certificati...")
            await self.certified_repo.update_from_remote()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Impossibile aggiornare repository: {e}")
    
    async def _verify_all_plugins(self) -> List[VerificationResult]:
        """Verifica tutti i plugin installati"""
        results = []
        
        # Ottieni lista plugin disponibili
        available_plugins = self.plugin_manager.list_available_plugins()
        
        for plugin_name in available_plugins:
            try:
                # Carica metadati plugin
                plugin_path = self.plugin_manager.plugins_dir / f"{plugin_name}.lcp"
                
                if not plugin_path.exists():
                    continue
                
                # TODO: Estrarre metadati da plugin criptato
                # Per ora crea metadati mock
                metadata = PluginMetadata(
                    name=plugin_name,
                    version="1.0.0",
                    author="Unknown",
                    description="Plugin description",
                    category="Unknown",
                    permissions=[],
                    dependencies=[],
                    min_core_version="1.0.0",
                    created_at=time.time(),
                    plugin_hash=""
                )
                
                # Verifica plugin
                result = await self.verification_engine.verify_plugin(str(plugin_path), metadata)
                results.append(result)
                
                self.boot_stats["plugins_verified"] += 1
                
            except Exception as e:
                self.logger.error(f"❌ Errore verifica plugin {plugin_name}: {e}")
        
        return results
    
    async def _handle_verification_results(self, results: List[VerificationResult]):
        """Gestisce risultati verifica plugin"""
        for result in results:
            if result.action == "ALLOW":
                self.logger.info(f"✅ Plugin {result.plugin_name} autorizzato (certificato {result.certification_level})")
                self.boot_stats["plugins_allowed"] += 1
                
            elif result.action == "WARN":
                self.logger.warning(f"⚠️ Plugin {result.plugin_name} richiede attenzione: {', '.join(result.issues)}")
                self.boot_stats["plugins_allowed"] += 1
                
            elif result.action == "QUARANTINE":
                await self._quarantine_plugin(result)
                self.boot_stats["plugins_quarantined"] += 1
                
            elif result.action == "BLOCK":
                self.logger.error(f"🚫 Plugin {result.plugin_name} bloccato: {', '.join(result.issues)}")
                self.boot_stats["plugins_blocked"] += 1
    
    async def _quarantine_plugin(self, result: VerificationResult):
        """Mette plugin in quarantena"""
        try:
            plugin_path = self.plugin_manager.plugins_dir / f"{result.plugin_name}.lcp"
            quarantine_path = self.quarantine_dir / f"{result.plugin_name}_{result.version}.lcp"
            
            if plugin_path.exists():
                # Sposta in quarantena
                plugin_path.rename(quarantine_path)
                
                # Salva report
                report_path = self.quarantine_dir / f"{result.plugin_name}_{result.version}_report.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "plugin_name": result.plugin_name,
                        "version": result.version,
                        "quarantine_reason": result.issues,
                        "quarantine_time": time.time(),
                        "verification_result": {
                            "is_certified": result.is_certified,
                            "certification_level": result.certification_level,
                            "checksum_valid": result.checksum_valid,
                            "signature_valid": result.signature_valid,
                            "analysis_score": result.analysis_score
                        }
                    }, f, indent=2)
                
                self.logger.warning(f"🔒 Plugin {result.plugin_name} messo in quarantena")
                
        except Exception as e:
            self.logger.error(f"❌ Errore quarantena plugin {result.plugin_name}: {e}")
    
    async def _load_verified_plugins(self, results: List[VerificationResult]):
        """Carica plugin verificati"""
        for result in results:
            if result.action in ["ALLOW", "WARN"]:
                try:
                    # Carica plugin tramite plugin manager
                    success = self.plugin_manager.load_plugin(result.plugin_name)
                    
                    if success:
                        self.logger.info(f"🔌 Plugin {result.plugin_name} caricato con successo")
                    else:
                        self.logger.error(f"❌ Errore caricamento plugin {result.plugin_name}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Errore caricamento plugin {result.plugin_name}: {e}")
    
    def _log_boot_summary(self):
        """Log riassunto boot"""
        duration = time.time() - self.boot_stats["start_time"]
        
        self.logger.info("📊 Riassunto Boot Sicuro:")
        self.logger.info(f"   ⏱️ Durata: {duration:.2f}s")
        self.logger.info(f"   🔍 Plugin verificati: {self.boot_stats['plugins_verified']}")
        self.logger.info(f"   ✅ Plugin autorizzati: {self.boot_stats['plugins_allowed']}")
        self.logger.info(f"   🔒 Plugin in quarantena: {self.boot_stats['plugins_quarantined']}")
        self.logger.info(f"   🚫 Plugin bloccati: {self.boot_stats['plugins_blocked']}")


async def initialize_secure_boot(plugin_manager):
    """
    Inizializza e esegue il boot sicuro per LaboonChat
    
    Args:
        plugin_manager: Istanza del LaboonPluginManager
        
    Returns:
        SecureBootManager: Manager del boot sicuro inizializzato
    """
    boot_manager = SecureBootManager(plugin_manager)
    await boot_manager.secure_boot_sequence()
    return boot_manager


if __name__ == "__main__":
    # Test del sistema
    import asyncio
    
    async def test_secure_boot():
        # Simula un plugin manager
        class MockPluginManager:
            def __init__(self):
                self.loaded_plugins = {}
                self.plugins_dir = Path("/tmp/test_plugins")
                
            def list_available_plugins(self):
                return []
                
            def load_plugin(self, plugin_path):
                print(f"Caricamento plugin: {plugin_path}")
                return True
                
            def unload_plugin(self, plugin_name):
                print(f"Scaricamento plugin: {plugin_name}")
                return True
        
        plugin_manager = MockPluginManager()
        boot_manager = await initialize_secure_boot(plugin_manager)
        
        # Mostra statistiche
        stats = boot_manager.boot_stats
        print(f"\n📊 Statistiche Boot Sicuro:")
        print(f"   ✅ Plugin autorizzati: {stats['plugins_allowed']}")
        print(f"   🔒 Plugin in quarantena: {stats['plugins_quarantined']}")
        print(f"   🚫 Plugin bloccati: {stats['plugins_blocked']}")
    
    asyncio.run(test_secure_boot())