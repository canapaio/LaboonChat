#!/usr/bin/env python3
"""
🤖 AI Code Verifier Plugin per LaboonChat
==========================================

Plugin di verifica intelligente che utilizza AI (Ollama, OpenAI, Claude) 
per analizzare automaticamente la sicurezza del codice dei plugin.

Caratteristiche:
- Integrazione con Ollama per analisi locale
- Supporto API esterne (OpenAI, Claude, Gemini)
- System prompt specializzato per sicurezza
- Analisi statica avanzata con AI
- Fallback intelligente tra diversi provider
- Cache dei risultati per performance
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import aiohttp
import ast
import re

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Provider AI supportati"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    LOCAL_ONLY = "local_only"

class SecurityLevel(Enum):
    """Livelli di sicurezza determinati dall'AI"""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"
    MALICIOUS = "malicious"
    UNKNOWN = "unknown"

@dataclass
class AIAnalysisResult:
    """Risultato dell'analisi AI"""
    security_level: SecurityLevel
    confidence: float  # 0.0 - 1.0
    issues_found: List[str]
    recommendations: List[str]
    analysis_summary: str
    provider_used: AIProvider
    analysis_time: float
    code_hash: str

class AICodeVerifier:
    """
    Verificatore di codice basato su AI per plugin LaboonChat
    
    Utilizza diversi provider AI per analizzare la sicurezza del codice
    con fallback intelligente e caching dei risultati.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "ai-verifier-config.json"
        self.cache_db = "ai_analysis_cache.db"
        self.config = self._load_config()
        self._init_cache_db()
        
        # System prompt specializzato per sicurezza plugin
        self.security_prompt = self._load_security_prompt()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carica configurazione AI providers"""
        default_config = {
            "providers": {
                "ollama": {
                    "enabled": True,
                    "url": "http://localhost:11434",
                    "model": "codellama:7b",
                    "timeout": 30,
                    "priority": 1
                },
                "openai": {
                    "enabled": False,
                    "api_key": "",
                    "model": "gpt-4",
                    "timeout": 20,
                    "priority": 2
                },
                "claude": {
                    "enabled": False,
                    "api_key": "",
                    "model": "claude-3-sonnet-20240229",
                    "timeout": 25,
                    "priority": 3
                }
            },
            "analysis": {
                "cache_duration_hours": 24,
                "min_confidence_threshold": 0.7,
                "enable_static_analysis": True,
                "max_file_size_kb": 500
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge con default config
                    default_config.update(user_config)
            else:
                # Crea config di default
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
                    
        except Exception as e:
            logger.warning(f"Errore caricamento config: {e}, uso default")
            
        return default_config
    
    def _init_cache_db(self):
        """Inizializza database cache risultati"""
        try:
            conn = sqlite3.connect(self.cache_db)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis_cache (
                    code_hash TEXT PRIMARY KEY,
                    security_level TEXT,
                    confidence REAL,
                    issues_found TEXT,
                    recommendations TEXT,
                    analysis_summary TEXT,
                    provider_used TEXT,
                    analysis_time REAL,
                    created_at INTEGER
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Errore inizializzazione cache DB: {e}")
    
    def _load_security_prompt(self) -> str:
        """Carica system prompt specializzato per sicurezza plugin"""
        return """
# 🛡️ AI Security Analyst per Plugin LaboonChat

Sei un esperto analista di sicurezza specializzato nell'analisi di plugin per sistemi di messaggistica P2P.

## 🎯 OBIETTIVO
Analizza il codice Python fornito per identificare potenziali rischi di sicurezza, vulnerabilità e comportamenti malevoli.

## 🔍 AREE DI ANALISI CRITICA

### 🚨 RISCHI CRITICI (MALICIOUS)
- Accesso non autorizzato a file di sistema
- Esecuzione di comandi shell pericolosi
- Connessioni di rete sospette
- Manipolazione di chiavi crittografiche
- Tentativi di privilege escalation
- Codice offuscato o nascosto

### ⚠️ RISCHI ELEVATI (DANGEROUS)
- Accesso a dati sensibili utente
- Modifiche non autorizzate a configurazioni
- Uso improprio di API di sistema
- Gestione insicura di dati crittografici
- Potenziali memory leaks o DoS

### 🟡 RISCHI MEDI (SUSPICIOUS)
- Pattern di codice insoliti
- Dipendenze esterne non verificate
- Gestione errori inadeguata
- Logging eccessivo di dati sensibili
- Performance issues potenziali

### ✅ SICURO (SAFE)
- Codice ben strutturato e documentato
- Uso appropriato delle API LaboonChat
- Gestione sicura degli errori
- Nessun accesso a risorse critiche
- Conformità alle best practices

## 📋 FORMATO RISPOSTA
Rispondi SEMPRE in formato JSON:

```json
{
    "security_level": "safe|suspicious|dangerous|malicious",
    "confidence": 0.95,
    "issues_found": [
        "Descrizione specifica del problema trovato",
        "Altro problema identificato"
    ],
    "recommendations": [
        "Raccomandazione specifica per migliorare la sicurezza",
        "Altra raccomandazione"
    ],
    "analysis_summary": "Riassunto conciso dell'analisi in 2-3 frasi"
}
```

## 🎯 FOCUS SPECIALE
- Plugin per sistemi P2P decentralizzati
- Sicurezza crittografica end-to-end
- Protezione privacy utenti
- Resistenza a censura e sorveglianza
- Integrità rete distribuita

Analizza il codice con massima attenzione ai dettagli di sicurezza.
"""

    def _calculate_code_hash(self, code: str) -> str:
        """Calcola hash del codice per caching"""
        return hashlib.sha256(code.encode('utf-8')).hexdigest()
    
    def _get_cached_result(self, code_hash: str) -> Optional[AIAnalysisResult]:
        """Recupera risultato dalla cache se valido"""
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            
            # Controlla cache validity
            cache_duration = self.config["analysis"]["cache_duration_hours"] * 3600
            min_timestamp = int(time.time()) - cache_duration
            
            cursor.execute('''
                SELECT * FROM ai_analysis_cache 
                WHERE code_hash = ? AND created_at > ?
            ''', (code_hash, min_timestamp))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return AIAnalysisResult(
                    security_level=SecurityLevel(row[1]),
                    confidence=row[2],
                    issues_found=json.loads(row[3]),
                    recommendations=json.loads(row[4]),
                    analysis_summary=row[5],
                    provider_used=AIProvider(row[6]),
                    analysis_time=row[7],
                    code_hash=row[0]
                )
                
        except Exception as e:
            logger.warning(f"Errore lettura cache: {e}")
            
        return None
    
    def _cache_result(self, result: AIAnalysisResult):
        """Salva risultato in cache"""
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_analysis_cache 
                (code_hash, security_level, confidence, issues_found, 
                 recommendations, analysis_summary, provider_used, 
                 analysis_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.code_hash,
                result.security_level.value,
                result.confidence,
                json.dumps(result.issues_found),
                json.dumps(result.recommendations),
                result.analysis_summary,
                result.provider_used.value,
                result.analysis_time,
                int(time.time())
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Errore salvataggio cache: {e}")
    
    async def _analyze_with_ollama(self, code: str) -> Optional[AIAnalysisResult]:
        """Analisi con Ollama (locale)"""
        config = self.config["providers"]["ollama"]
        if not config["enabled"]:
            return None
            
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": config["model"],
                    "prompt": f"{self.security_prompt}\n\n# CODICE DA ANALIZZARE:\n```python\n{code}\n```",
                    "stream": False
                }
                
                async with session.post(
                    f"{config['url']}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=config["timeout"])
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        analysis_text = data.get("response", "")
                        
                        # Parse JSON response
                        result = self._parse_ai_response(
                            analysis_text, 
                            AIProvider.OLLAMA,
                            time.time() - start_time,
                            code
                        )
                        
                        if result:
                            logger.info(f"✅ Analisi Ollama completata: {result.security_level.value}")
                            return result
                            
        except Exception as e:
            logger.warning(f"❌ Errore analisi Ollama: {e}")
            
        return None
    
    async def _analyze_with_openai(self, code: str) -> Optional[AIAnalysisResult]:
        """Analisi con OpenAI API"""
        config = self.config["providers"]["openai"]
        if not config["enabled"] or not config["api_key"]:
            return None
            
        try:
            start_time = time.time()
            
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config["model"],
                "messages": [
                    {"role": "system", "content": self.security_prompt},
                    {"role": "user", "content": f"Analizza questo codice Python:\n```python\n{code}\n```"}
                ],
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=config["timeout"])
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        analysis_text = data["choices"][0]["message"]["content"]
                        
                        result = self._parse_ai_response(
                            analysis_text,
                            AIProvider.OPENAI,
                            time.time() - start_time,
                            code
                        )
                        
                        if result:
                            logger.info(f"✅ Analisi OpenAI completata: {result.security_level.value}")
                            return result
                            
        except Exception as e:
            logger.warning(f"❌ Errore analisi OpenAI: {e}")
            
        return None
    
    def _parse_ai_response(self, response_text: str, provider: AIProvider, 
                          analysis_time: float, code: str) -> Optional[AIAnalysisResult]:
        """Parse della risposta AI in formato JSON"""
        try:
            # Estrai JSON dalla risposta
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Prova a trovare JSON diretto
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    raise ValueError("Nessun JSON trovato nella risposta")
            
            data = json.loads(json_text)
            
            return AIAnalysisResult(
                security_level=SecurityLevel(data["security_level"]),
                confidence=float(data["confidence"]),
                issues_found=data.get("issues_found", []),
                recommendations=data.get("recommendations", []),
                analysis_summary=data.get("analysis_summary", ""),
                provider_used=provider,
                analysis_time=analysis_time,
                code_hash=self._calculate_code_hash(code)
            )
            
        except Exception as e:
            logger.error(f"Errore parsing risposta AI: {e}")
            return None
    
    def _static_analysis(self, code: str) -> List[str]:
        """Analisi statica di base del codice"""
        issues = []
        
        try:
            # Parse AST per analisi strutturale
            tree = ast.parse(code)
            
            # Controlla import pericolosi
            dangerous_imports = ['os', 'subprocess', 'sys', 'socket', 'urllib', 'requests']
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in dangerous_imports:
                            issues.append(f"Import potenzialmente pericoloso: {alias.name}")
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module in dangerous_imports:
                        issues.append(f"Import da modulo pericoloso: {node.module}")
            
            # Controlla pattern sospetti nel codice
            suspicious_patterns = [
                (r'eval\s*\(', "Uso di eval() - rischio esecuzione codice arbitrario"),
                (r'exec\s*\(', "Uso di exec() - rischio esecuzione codice arbitrario"),
                (r'__import__\s*\(', "Uso di __import__() - caricamento dinamico moduli"),
                (r'open\s*\([^)]*["\']\/[^"\']*["\']', "Accesso a file di sistema assoluti"),
                (r'subprocess\.(call|run|Popen)', "Esecuzione comandi di sistema"),
                (r'socket\.socket', "Creazione connessioni di rete"),
            ]
            
            for pattern, description in suspicious_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    issues.append(description)
                    
        except SyntaxError as e:
            issues.append(f"Errore sintassi Python: {e}")
        except Exception as e:
            issues.append(f"Errore analisi statica: {e}")
            
        return issues
    
    async def analyze_plugin_code(self, code: str, plugin_name: str = "unknown") -> AIAnalysisResult:
        """
        Analizza il codice di un plugin per sicurezza
        
        Args:
            code: Codice Python del plugin
            plugin_name: Nome del plugin per logging
            
        Returns:
            AIAnalysisResult con risultati dell'analisi
        """
        logger.info(f"🔍 Inizio analisi plugin: {plugin_name}")
        
        # Controlla dimensione file
        max_size = self.config["analysis"]["max_file_size_kb"] * 1024
        if len(code.encode('utf-8')) > max_size:
            return AIAnalysisResult(
                security_level=SecurityLevel.SUSPICIOUS,
                confidence=0.8,
                issues_found=["File troppo grande per analisi sicura"],
                recommendations=["Ridurre dimensione del plugin"],
                analysis_summary="Plugin rifiutato per dimensioni eccessive",
                provider_used=AIProvider.LOCAL_ONLY,
                analysis_time=0.0,
                code_hash=self._calculate_code_hash(code)
            )
        
        # Controlla cache
        code_hash = self._calculate_code_hash(code)
        cached_result = self._get_cached_result(code_hash)
        if cached_result:
            logger.info(f"📋 Risultato da cache: {cached_result.security_level.value}")
            return cached_result
        
        # Analisi statica locale
        static_issues = []
        if self.config["analysis"]["enable_static_analysis"]:
            static_issues = self._static_analysis(code)
        
        # Prova analisi AI con fallback tra provider
        providers = sorted(
            [(name, config) for name, config in self.config["providers"].items() if config["enabled"]],
            key=lambda x: x[1]["priority"]
        )
        
        ai_result = None
        for provider_name, provider_config in providers:
            try:
                if provider_name == "ollama":
                    ai_result = await self._analyze_with_ollama(code)
                elif provider_name == "openai":
                    ai_result = await self._analyze_with_openai(code)
                # Aggiungi altri provider qui
                
                if ai_result and ai_result.confidence >= self.config["analysis"]["min_confidence_threshold"]:
                    break
                    
            except Exception as e:
                logger.warning(f"Errore provider {provider_name}: {e}")
                continue
        
        # Fallback se nessuna AI disponibile
        if not ai_result:
            security_level = SecurityLevel.SUSPICIOUS if static_issues else SecurityLevel.SAFE
            ai_result = AIAnalysisResult(
                security_level=security_level,
                confidence=0.6,
                issues_found=static_issues,
                recommendations=["Verifica manuale raccomandata - AI non disponibile"],
                analysis_summary="Analisi solo statica - AI non disponibile",
                provider_used=AIProvider.LOCAL_ONLY,
                analysis_time=0.1,
                code_hash=code_hash
            )
        else:
            # Combina risultati AI + analisi statica
            ai_result.issues_found.extend(static_issues)
        
        # Cache del risultato
        self._cache_result(ai_result)
        
        logger.info(f"✅ Analisi completata: {ai_result.security_level.value} (confidence: {ai_result.confidence:.2f})")
        return ai_result

# Funzioni di utilità per integrazione
async def verify_plugin_with_ai(plugin_path: str, config_path: Optional[str] = None) -> AIAnalysisResult:
    """Funzione di utilità per verificare un plugin"""
    verifier = AICodeVerifier(config_path)
    
    with open(plugin_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    plugin_name = Path(plugin_path).stem
    return await verifier.analyze_plugin_code(code, plugin_name)

def get_security_recommendation(result: AIAnalysisResult) -> str:
    """Ottieni raccomandazione di sicurezza basata sul risultato"""
    if result.security_level == SecurityLevel.SAFE:
        return "✅ Plugin sicuro - installazione automatica"
    elif result.security_level == SecurityLevel.SUSPICIOUS:
        return "⚠️ Plugin sospetto - richiede conferma utente"
    elif result.security_level == SecurityLevel.DANGEROUS:
        return "🚫 Plugin pericoloso - installazione sconsigliata"
    elif result.security_level == SecurityLevel.MALICIOUS:
        return "🔴 Plugin malevolo - installazione bloccata"
    else:
        return "❓ Plugin non analizzabile - verifica manuale richiesta"

if __name__ == "__main__":
    # Test del sistema
    import sys
    
    async def test_verifier():
        if len(sys.argv) > 1:
            plugin_path = sys.argv[1]
            result = await verify_plugin_with_ai(plugin_path)
            
            print(f"\n🔍 Analisi Plugin: {Path(plugin_path).name}")
            print(f"🛡️ Livello Sicurezza: {result.security_level.value}")
            print(f"📊 Confidence: {result.confidence:.2f}")
            print(f"⚡ Provider: {result.provider_used.value}")
            print(f"⏱️ Tempo: {result.analysis_time:.2f}s")
            
            if result.issues_found:
                print(f"\n⚠️ Problemi trovati:")
                for issue in result.issues_found:
                    print(f"  - {issue}")
            
            if result.recommendations:
                print(f"\n💡 Raccomandazioni:")
                for rec in result.recommendations:
                    print(f"  - {rec}")
            
            print(f"\n📝 Riassunto: {result.analysis_summary}")
            print(f"\n{get_security_recommendation(result)}")
        else:
            print("Uso: python ai-code-verifier.py <path_to_plugin.py>")
    
    asyncio.run(test_verifier())