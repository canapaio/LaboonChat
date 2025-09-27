"""
🛡️ LaboonChat Parental Network Protection - Sistema Auto-Protezione Distribuito
==============================================================================

Sistema innovativo di protezione automatica basato sulla rete parentale dei contatti.
La sicurezza emerge dal comportamento collettivo della rete, non da controlli centrali.

🐋 "La saggezza della comunità protegge ogni Laboon" 🌊

Features:
- Logging distribuito di tutte le azioni utente
- Rilevamento anomalie tramite consenso di rete
- Auto-moderazione basata su reputazione distribuita
- Sistema immunitario digitale emergente
- Protezione senza friction per utenti onesti

Author: LaboonChat Team
License: GPL-3.0
"""

import json
import time
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserAction:
    """Rappresenta un'azione utente loggata nella rete"""
    user_id: str
    action_type: str  # 'message', 'connect', 'file_transfer', etc.
    timestamp: float
    context: Dict[str, Any]
    peer_witnesses: List[str]  # Lista di peer che hanno osservato l'azione
    severity: int = 1  # 1=normale, 2=sospetto, 3=dannoso
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserAction':
        return cls(**data)

@dataclass
class AnomalyReport:
    """Report di anomalia rilevata dalla rete"""
    user_id: str
    anomaly_type: str
    confidence: float  # 0.0-1.0
    evidence: List[UserAction]
    reporting_peers: List[str]
    timestamp: float
    recommended_action: str  # 'monitor', 'limit', 'isolate', 'ban'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'anomaly_type': self.anomaly_type,
            'confidence': self.confidence,
            'evidence': [action.to_dict() for action in self.evidence],
            'reporting_peers': self.reporting_peers,
            'timestamp': self.timestamp,
            'recommended_action': self.recommended_action
        }

@dataclass
class TrustScore:
    """Punteggio di fiducia distribuito per un utente"""
    user_id: str
    score: float  # 0.0-1.0 (0=banned, 1=trusted)
    last_updated: float
    contributing_peers: List[str]
    recent_actions: int
    anomaly_count: int
    
    def is_trusted(self) -> bool:
        return self.score >= 0.7
    
    def is_suspicious(self) -> bool:
        return 0.3 <= self.score < 0.7
    
    def is_dangerous(self) -> bool:
        return self.score < 0.3

class BehaviorAnalyzer:
    """Analizza comportamenti utente per rilevare anomalie"""
    
    def __init__(self):
        self.normal_patterns = {}
        self.anomaly_thresholds = {
            'message_frequency': 50,  # messaggi/ora
            'connection_frequency': 20,  # connessioni/ora
            'file_transfer_size': 1024 * 1024 * 100,  # 100MB/ora
            'peer_diversity': 0.1,  # minima diversità peer
        }
    
    def analyze_user_behavior(self, user_id: str, recent_actions: List[UserAction]) -> Optional[AnomalyReport]:
        """Analizza comportamento utente e rileva anomalie"""
        if not recent_actions:
            return None
        
        # Analisi frequenza messaggi
        message_actions = [a for a in recent_actions if a.action_type == 'message']
        if len(message_actions) > self.anomaly_thresholds['message_frequency']:
            return AnomalyReport(
                user_id=user_id,
                anomaly_type='spam_flooding',
                confidence=0.8,
                evidence=message_actions[-10:],  # Ultimi 10 messaggi come evidenza
                reporting_peers=[],
                timestamp=time.time(),
                recommended_action='limit'
            )
        
        # Analisi connessioni eccessive
        connect_actions = [a for a in recent_actions if a.action_type == 'connect']
        if len(connect_actions) > self.anomaly_thresholds['connection_frequency']:
            return AnomalyReport(
                user_id=user_id,
                anomaly_type='connection_flooding',
                confidence=0.7,
                evidence=connect_actions[-5:],
                reporting_peers=[],
                timestamp=time.time(),
                recommended_action='monitor'
            )
        
        # Analisi pattern temporali sospetti
        if self._detect_bot_pattern(recent_actions):
            return AnomalyReport(
                user_id=user_id,
                anomaly_type='bot_behavior',
                confidence=0.9,
                evidence=recent_actions[-5:],
                reporting_peers=[],
                timestamp=time.time(),
                recommended_action='isolate'
            )
        
        return None
    
    def _detect_bot_pattern(self, actions: List[UserAction]) -> bool:
        """Rileva pattern di comportamento bot-like"""
        if len(actions) < 5:
            return False
        
        # Controlla intervalli troppo regolari
        intervals = []
        for i in range(1, len(actions)):
            interval = actions[i].timestamp - actions[i-1].timestamp
            intervals.append(interval)
        
        # Se tutti gli intervalli sono quasi identici, potrebbe essere un bot
        if len(set(round(interval, 1) for interval in intervals)) == 1:
            return True
        
        return False

class NetworkConsensus:
    """Gestisce il consenso distribuito della rete per decisioni di sicurezza"""
    
    def __init__(self):
        self.peer_votes = defaultdict(list)
        self.consensus_threshold = 0.6  # 60% dei peer devono concordare
    
    async def submit_anomaly_vote(self, peer_id: str, anomaly_report: AnomalyReport) -> bool:
        """Peer sottomette voto su anomalia rilevata"""
        vote_key = f"{anomaly_report.user_id}_{anomaly_report.anomaly_type}"
        
        # Aggiungi voto del peer
        self.peer_votes[vote_key].append({
            'peer_id': peer_id,
            'confidence': anomaly_report.confidence,
            'timestamp': time.time(),
            'recommended_action': anomaly_report.recommended_action
        })
        
        # Pulisci voti vecchi (>1 ora)
        cutoff_time = time.time() - 3600
        self.peer_votes[vote_key] = [
            vote for vote in self.peer_votes[vote_key] 
            if vote['timestamp'] > cutoff_time
        ]
        
        return await self._check_consensus(vote_key)
    
    async def _check_consensus(self, vote_key: str) -> bool:
        """Controlla se c'è consenso sufficiente per azione"""
        votes = self.peer_votes[vote_key]
        if len(votes) < 3:  # Minimo 3 peer per consenso
            return False
        
        # Calcola consenso pesato per confidenza
        total_confidence = sum(vote['confidence'] for vote in votes)
        avg_confidence = total_confidence / len(votes)
        
        # Consenso raggiunto se confidenza media > soglia
        return avg_confidence >= self.consensus_threshold
    
    def get_consensus_action(self, vote_key: str) -> Optional[str]:
        """Ottieni azione consensuale per anomalia"""
        votes = self.peer_votes[vote_key]
        if not votes:
            return None
        
        # Conta voti per azione
        action_counts = defaultdict(int)
        for vote in votes:
            action_counts[vote['recommended_action']] += 1
        
        # Ritorna azione più votata
        return max(action_counts.items(), key=lambda x: x[1])[0]

class DistributedReputation:
    """Sistema di reputazione distribuito basato su consenso rete"""
    
    def __init__(self, data_dir: str = "reputation"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.trust_scores: Dict[str, TrustScore] = {}
        self.reputation_file = self.data_dir / "trust_scores.json"
        self._load_reputation()
    
    def _load_reputation(self):
        """Carica punteggi di reputazione salvati"""
        if self.reputation_file.exists():
            try:
                with open(self.reputation_file, 'r') as f:
                    data = json.load(f)
                    for user_id, score_data in data.items():
                        self.trust_scores[user_id] = TrustScore(**score_data)
                logger.info(f"Loaded reputation for {len(self.trust_scores)} users")
            except Exception as e:
                logger.error(f"Error loading reputation: {e}")
    
    def _save_reputation(self):
        """Salva punteggi di reputazione"""
        try:
            data = {
                user_id: asdict(score) 
                for user_id, score in self.trust_scores.items()
            }
            with open(self.reputation_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reputation: {e}")
    
    def get_trust_score(self, user_id: str) -> TrustScore:
        """Ottieni punteggio di fiducia per utente"""
        if user_id not in self.trust_scores:
            # Nuovo utente inizia con fiducia media
            self.trust_scores[user_id] = TrustScore(
                user_id=user_id,
                score=0.5,  # Fiducia neutra iniziale
                last_updated=time.time(),
                contributing_peers=[],
                recent_actions=0,
                anomaly_count=0
            )
        return self.trust_scores[user_id]
    
    def update_trust_score(self, user_id: str, anomaly_report: Optional[AnomalyReport], 
                          positive_feedback: bool = False):
        """Aggiorna punteggio di fiducia basato su feedback rete"""
        trust_score = self.get_trust_score(user_id)
        
        if anomaly_report:
            # Diminuisci fiducia per anomalie
            penalty = anomaly_report.confidence * 0.2
            trust_score.score = max(0.0, trust_score.score - penalty)
            trust_score.anomaly_count += 1
        elif positive_feedback:
            # Aumenta fiducia per comportamento positivo
            bonus = 0.05
            trust_score.score = min(1.0, trust_score.score + bonus)
        
        trust_score.last_updated = time.time()
        trust_score.recent_actions += 1
        
        # Salva aggiornamenti
        self._save_reputation()
        
        logger.info(f"Updated trust score for {user_id}: {trust_score.score:.2f}")

class ParentalNetworkProtection:
    """Sistema principale di auto-protezione tramite rete parentale"""
    
    def __init__(self, data_dir: str = "parental_protection"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Componenti del sistema
        self.behavior_analyzer = BehaviorAnalyzer()
        self.network_consensus = NetworkConsensus()
        self.reputation_system = DistributedReputation(str(self.data_dir / "reputation"))
        
        # Storage azioni utente
        self.user_actions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.actions_file = self.data_dir / "user_actions.json"
        
        # Configurazione
        self.monitoring_window = 3600  # 1 ora
        self.max_actions_per_user = 1000
        
        self._load_user_actions()
        
        logger.info("ParentalNetworkProtection initialized")
    
    def _load_user_actions(self):
        """Carica azioni utente salvate"""
        if self.actions_file.exists():
            try:
                with open(self.actions_file, 'r') as f:
                    data = json.load(f)
                    for user_id, actions_data in data.items():
                        actions = deque(maxlen=self.max_actions_per_user)
                        for action_data in actions_data:
                            actions.append(UserAction.from_dict(action_data))
                        self.user_actions[user_id] = actions
                logger.info(f"Loaded actions for {len(self.user_actions)} users")
            except Exception as e:
                logger.error(f"Error loading user actions: {e}")
    
    def _save_user_actions(self):
        """Salva azioni utente"""
        try:
            data = {}
            for user_id, actions in self.user_actions.items():
                # Salva solo azioni recenti (ultima ora)
                cutoff_time = time.time() - self.monitoring_window
                recent_actions = [
                    action.to_dict() for action in actions 
                    if action.timestamp > cutoff_time
                ]
                if recent_actions:
                    data[user_id] = recent_actions
            
            with open(self.actions_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user actions: {e}")
    
    async def log_user_action(self, user_id: str, action_type: str, 
                            context: Dict[str, Any], peer_witnesses: List[str] = None):
        """Logga azione utente nella rete parentale"""
        action = UserAction(
            user_id=user_id,
            action_type=action_type,
            timestamp=time.time(),
            context=context,
            peer_witnesses=peer_witnesses or [],
            severity=1
        )
        
        # Aggiungi azione alla cronologia utente
        self.user_actions[user_id].append(action)
        
        # Analizza comportamento per anomalie
        await self._analyze_and_respond(user_id)
        
        # Salva periodicamente
        if len(self.user_actions[user_id]) % 50 == 0:
            self._save_user_actions()
        
        logger.debug(f"Logged action for {user_id}: {action_type}")
    
    async def _analyze_and_respond(self, user_id: str):
        """Analizza comportamento utente e risponde ad anomalie"""
        # Ottieni azioni recenti
        cutoff_time = time.time() - self.monitoring_window
        recent_actions = [
            action for action in self.user_actions[user_id]
            if action.timestamp > cutoff_time
        ]
        
        # Analizza per anomalie
        anomaly_report = self.behavior_analyzer.analyze_user_behavior(user_id, recent_actions)
        
        if anomaly_report:
            logger.warning(f"Anomaly detected for {user_id}: {anomaly_report.anomaly_type}")
            
            # Sottometti a consenso rete
            consensus_reached = await self.network_consensus.submit_anomaly_vote(
                "local_peer", anomaly_report
            )
            
            if consensus_reached:
                # Applica azione consensuale
                await self._apply_protection_action(user_id, anomaly_report)
            
            # Aggiorna reputazione
            self.reputation_system.update_trust_score(user_id, anomaly_report)
        else:
            # Comportamento normale, piccolo bonus reputazione
            if len(recent_actions) > 10:  # Solo se abbastanza attivo
                self.reputation_system.update_trust_score(user_id, None, positive_feedback=True)
    
    async def _apply_protection_action(self, user_id: str, anomaly_report: AnomalyReport):
        """Applica azione di protezione basata su consenso rete"""
        action = anomaly_report.recommended_action
        
        logger.warning(f"Applying protection action '{action}' for user {user_id}")
        
        if action == 'monitor':
            # Aumenta monitoraggio
            pass  # Già implementato tramite logging
        
        elif action == 'limit':
            # Applica rate limiting
            await self._apply_rate_limiting(user_id)
        
        elif action == 'isolate':
            # Isola temporaneamente dalla rete
            await self._apply_temporary_isolation(user_id)
        
        elif action == 'ban':
            # Ban permanente
            await self._apply_permanent_ban(user_id)
    
    async def _apply_rate_limiting(self, user_id: str):
        """Applica rate limiting per utente"""
        # Implementazione rate limiting
        logger.info(f"Rate limiting applied to {user_id}")
        # TODO: Integrazione con sistema di messaging
    
    async def _apply_temporary_isolation(self, user_id: str):
        """Isola temporaneamente utente dalla rete"""
        logger.info(f"Temporary isolation applied to {user_id}")
        # TODO: Integrazione con sistema P2P
    
    async def _apply_permanent_ban(self, user_id: str):
        """Ban permanente utente"""
        logger.critical(f"Permanent ban applied to {user_id}")
        # TODO: Integrazione con sistema di identità
    
    def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Ottieni status di sicurezza per utente"""
        trust_score = self.reputation_system.get_trust_score(user_id)
        recent_actions = len([
            action for action in self.user_actions[user_id]
            if action.timestamp > time.time() - self.monitoring_window
        ])
        
        return {
            'user_id': user_id,
            'trust_score': trust_score.score,
            'trust_level': 'trusted' if trust_score.is_trusted() else 
                          'suspicious' if trust_score.is_suspicious() else 'dangerous',
            'recent_actions': recent_actions,
            'anomaly_count': trust_score.anomaly_count,
            'last_updated': trust_score.last_updated
        }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche della rete di protezione"""
        total_users = len(self.user_actions)
        trusted_users = sum(1 for user_id in self.user_actions.keys() 
                           if self.reputation_system.get_trust_score(user_id).is_trusted())
        suspicious_users = sum(1 for user_id in self.user_actions.keys() 
                              if self.reputation_system.get_trust_score(user_id).is_suspicious())
        dangerous_users = sum(1 for user_id in self.user_actions.keys() 
                             if self.reputation_system.get_trust_score(user_id).is_dangerous())
        
        return {
            'total_users': total_users,
            'trusted_users': trusted_users,
            'suspicious_users': suspicious_users,
            'dangerous_users': dangerous_users,
            'protection_active': True,
            'monitoring_window_hours': self.monitoring_window / 3600
        }

# Singleton instance
_parental_protection_instance = None

def get_parental_protection() -> ParentalNetworkProtection:
    """Ottieni istanza singleton del sistema di protezione"""
    global _parental_protection_instance
    if _parental_protection_instance is None:
        _parental_protection_instance = ParentalNetworkProtection()
    return _parental_protection_instance

# Convenience functions
async def log_user_action(user_id: str, action_type: str, context: Dict[str, Any], 
                         peer_witnesses: List[str] = None):
    """Log user action in parental network"""
    protection = get_parental_protection()
    await protection.log_user_action(user_id, action_type, context, peer_witnesses)

def get_user_trust_score(user_id: str) -> float:
    """Get user trust score (0.0-1.0)"""
    protection = get_parental_protection()
    return protection.reputation_system.get_trust_score(user_id).score

def is_user_trusted(user_id: str) -> bool:
    """Check if user is trusted by the network"""
    return get_user_trust_score(user_id) >= 0.7

if __name__ == "__main__":
    # Test del sistema
    async def test_parental_protection():
        print("🛡️ Testing Parental Network Protection...")
        
        protection = ParentalNetworkProtection("test_parental_protection")
        
        # Simula comportamento normale
        await protection.log_user_action("user1", "message", {"content": "Hello world"})
        await protection.log_user_action("user1", "connect", {"peer": "user2"})
        
        # Simula comportamento sospetto (spam)
        for i in range(60):  # 60 messaggi in poco tempo
            await protection.log_user_action("user2", "message", {"content": f"Spam {i}"})
        
        # Controlla status
        user1_status = protection.get_user_status("user1")
        user2_status = protection.get_user_status("user2")
        
        print(f"✅ User1 status: {user1_status}")
        print(f"⚠️ User2 status: {user2_status}")
        
        # Statistiche rete
        stats = protection.get_network_stats()
        print(f"📊 Network stats: {stats}")
        
        print("🛡️ Parental Network Protection test completed!")
    
    # Run test
    asyncio.run(test_parental_protection())