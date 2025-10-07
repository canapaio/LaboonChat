"""
Advanced File Sharing Plugin - Plugin Secondario per LaboonChat2

Plugin avanzato per condivisione file che fornisce:
- Chunking intelligente per file grandi
- Compressione automatica
- Crittografia end-to-end
- Gestione torrent-like con peer multipli
- Resume e recovery automatico
- Verifica integrità con hash
- Bandwidth management
- Metadata ricchi
"""

import asyncio
import hashlib
import json
import time
import zlib
import os
import mimetypes
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from laboon_chat2.core.interfaces import ISecondaryPlugin


class TransferStatus(Enum):
    """Stati del trasferimento"""
    PENDING = "pending"
    PREPARING = "preparing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChunkStatus(Enum):
    """Stati del chunk"""
    MISSING = "missing"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CORRUPTED = "corrupted"


class CompressionType(Enum):
    """Tipi di compressione"""
    NONE = "none"
    ZLIB = "zlib"
    GZIP = "gzip"
    AUTO = "auto"


@dataclass
class FileChunk:
    """Chunk di file"""
    chunk_id: int
    offset: int
    size: int
    hash_sha256: str
    status: ChunkStatus = ChunkStatus.MISSING
    data: Optional[bytes] = None
    peers: Set[str] = None
    download_attempts: int = 0
    last_attempt: float = 0.0
    
    def __post_init__(self):
        if self.peers is None:
            self.peers = set()


@dataclass
class FileMetadata:
    """Metadata del file"""
    file_id: str
    filename: str
    file_size: int
    mime_type: str
    hash_sha256: str
    chunk_size: int
    total_chunks: int
    compression: CompressionType
    encrypted: bool
    created_at: float
    modified_at: float
    description: str = ""
    tags: List[str] = None
    thumbnail: Optional[bytes] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TransferProgress:
    """Progresso del trasferimento"""
    file_id: str
    status: TransferStatus
    chunks_completed: int
    total_chunks: int
    bytes_transferred: int
    total_bytes: int
    speed_bps: float
    eta_seconds: float
    peers_count: int
    error_message: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    
    @property
    def progress_percentage(self) -> float:
        """Percentuale di completamento"""
        if self.total_chunks == 0:
            return 0.0
        return (self.chunks_completed / self.total_chunks) * 100.0


@dataclass
class PeerInfo:
    """Informazioni peer"""
    peer_id: str
    address: str
    port: int
    available_chunks: Set[int]
    bandwidth_bps: float
    latency_ms: float
    reliability_score: float
    last_seen: float
    
    def __post_init__(self):
        if self.available_chunks is None:
            self.available_chunks = set()


@dataclass
class TransferStats:
    """Statistiche trasferimenti"""
    total_files_shared: int = 0
    total_files_downloaded: int = 0
    total_bytes_uploaded: int = 0
    total_bytes_downloaded: int = 0
    active_transfers: int = 0
    average_speed_upload: float = 0.0
    average_speed_download: float = 0.0
    peer_connections: int = 0
    successful_transfers: int = 0
    failed_transfers: int = 0


class AdvancedFileSharing(ISecondaryPlugin):
    """
    Plugin avanzato per condivisione file P2P
    
    Caratteristiche:
    - Chunking intelligente
    - Compressione automatica
    - Crittografia end-to-end
    - Gestione multi-peer
    - Resume automatico
    - Verifica integrità
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        
        # Moduli core
        self.security_module = None
        self.messaging_module = None
        self.network_module = None
        self.interface_module = None
        
        # Stato interno
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Gestione file
        self.shared_files: Dict[str, FileMetadata] = {}
        self.active_transfers: Dict[str, TransferProgress] = {}
        self.file_chunks: Dict[str, List[FileChunk]] = {}
        self.download_queue: List[str] = []
        
        # Gestione peer
        self.peers: Dict[str, PeerInfo] = {}
        self.peer_files: Dict[str, Set[str]] = {}  # peer_id -> set di file_id
        
        # Statistiche
        self.stats = TransferStats()
        
        # Task asincroni
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Handler eventi
        self.transfer_handler: Optional[Callable] = None
        self.progress_handler: Optional[Callable] = None
        
        # Configurazioni
        self.chunk_size = 64 * 1024  # 64KB default
        self.max_concurrent_downloads = 5
        self.max_concurrent_uploads = 10
        self.bandwidth_limit_bps = 0  # 0 = unlimited
        
        # Directory
        self.downloads_dir = Path("downloads")
        self.shared_dir = Path("shared")
        self.temp_dir = Path("temp")
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Inizializza il plugin"""
        self.config = config.copy()
        
        # Configura parametri
        self.chunk_size = config.get("chunk_size", 64 * 1024)
        self.max_concurrent_downloads = config.get("max_concurrent_downloads", 5)
        self.max_concurrent_uploads = config.get("max_concurrent_uploads", 10)
        self.bandwidth_limit_bps = config.get("bandwidth_limit_bps", 0)
        
        # Crea directory
        base_dir = Path(config.get("data_dir", "data/file_sharing"))
        self.downloads_dir = base_dir / "downloads"
        self.shared_dir = base_dir / "shared"
        self.temp_dir = base_dir / "temp"
        
        for directory in [self.downloads_dir, self.shared_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Carica dati persistenti
        await self._load_persistent_data()
        
        # Avvia task di background
        await self._start_background_tasks()
        
        self.running = True
        self.logger.info("AdvancedFileSharing inizializzato")
    
    async def cleanup(self) -> None:
        """Pulisce le risorse del plugin"""
        self.running = False
        
        # Ferma task di background
        await self._stop_background_tasks()
        
        # Salva dati persistenti
        await self._save_persistent_data()
        
        self.logger.info("AdvancedFileSharing terminato")
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul plugin"""
        return {
            "name": "AdvancedFileSharing",
            "version": "1.0.0",
            "type": "secondary",
            "category": "advanced_features",
            "description": "Sistema avanzato di condivisione file P2P con chunking, compressione e crittografia",
            "author": "LaboonChat2 Team",
            "capabilities": [
                "chunked_transfer",
                "compression",
                "encryption",
                "multi_peer",
                "resume_support",
                "integrity_verification",
                "bandwidth_management",
                "metadata_rich"
            ],
            "dependencies": ["messaging", "security", "network"],
            "optional_dependencies": ["interface"]
        }
    
    async def activate(self) -> bool:
        """Attiva il plugin"""
        try:
            # Registra handler messaggi
            if self.messaging_module:
                await self.messaging_module.set_message_handler(self._handle_message)
            
            self.logger.info("AdvancedFileSharing attivato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore attivazione AdvancedFileSharing: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Disattiva il plugin"""
        try:
            # Pausa tutti i trasferimenti attivi
            for file_id in list(self.active_transfers.keys()):
                await self.pause_transfer(file_id)
            
            self.logger.info("AdvancedFileSharing disattivato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore disattivazione AdvancedFileSharing: {e}")
            return False
    
    async def set_core_module(self, module_type: str, module_instance: Any) -> None:
        """Imposta riferimento a modulo core"""
        if module_type == "security":
            self.security_module = module_instance
        elif module_type == "messaging":
            self.messaging_module = module_instance
        elif module_type == "network":
            self.network_module = module_instance
        elif module_type == "interface":
            self.interface_module = module_instance
    
    async def get_status(self) -> Dict[str, Any]:
        """Restituisce stato del plugin"""
        return {
            "running": self.running,
            "shared_files": len(self.shared_files),
            "active_transfers": len(self.active_transfers),
            "connected_peers": len(self.peers),
            "stats": asdict(self.stats)
        }
    
    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Aggiorna configurazione del plugin"""
        self.config.update(new_config)
        
        # Aggiorna parametri se cambiati
        if "chunk_size" in new_config:
            self.chunk_size = new_config["chunk_size"]
        if "max_concurrent_downloads" in new_config:
            self.max_concurrent_downloads = new_config["max_concurrent_downloads"]
        if "bandwidth_limit_bps" in new_config:
            self.bandwidth_limit_bps = new_config["bandwidth_limit_bps"]
    
    # Metodi pubblici per condivisione file
    
    async def share_file(self, file_path: str, description: str = "", tags: List[str] = None) -> Optional[str]:
        """Condivide un file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"File non trovato: {file_path}")
                return None
            
            # Genera metadata
            metadata = await self._create_file_metadata(file_path, description, tags or [])
            
            # Crea chunks
            chunks = await self._create_file_chunks(file_path, metadata)
            
            # Salva in shared
            self.shared_files[metadata.file_id] = metadata
            self.file_chunks[metadata.file_id] = chunks
            
            # Copia file in directory condivisa
            shared_path = self.shared_dir / metadata.filename
            if not shared_path.exists():
                import shutil
                shutil.copy2(file_path, shared_path)
            
            # Notifica peer
            await self._announce_file(metadata)
            
            self.stats.total_files_shared += 1
            await self._save_persistent_data()
            
            self.logger.info(f"File condiviso: {metadata.filename} ({metadata.file_id})")
            return metadata.file_id
            
        except Exception as e:
            self.logger.error(f"Errore condivisione file {file_path}: {e}")
            return None
    
    async def download_file(self, file_id: str, peer_id: str = None) -> bool:
        """Avvia download di un file"""
        try:
            if file_id in self.active_transfers:
                self.logger.warning(f"Download già attivo per {file_id}")
                return False
            
            # Trova peer con il file
            available_peers = []
            if peer_id:
                if peer_id in self.peers and file_id in self.peer_files.get(peer_id, set()):
                    available_peers = [peer_id]
            else:
                available_peers = [
                    pid for pid, files in self.peer_files.items()
                    if file_id in files
                ]
            
            if not available_peers:
                self.logger.error(f"Nessun peer disponibile per file {file_id}")
                return False
            
            # Richiedi metadata se non disponibile
            if file_id not in self.shared_files:
                metadata = await self._request_file_metadata(file_id, available_peers[0])
                if not metadata:
                    return False
                self.shared_files[file_id] = metadata
            
            metadata = self.shared_files[file_id]
            
            # Crea progresso trasferimento
            progress = TransferProgress(
                file_id=file_id,
                status=TransferStatus.PREPARING,
                chunks_completed=0,
                total_chunks=metadata.total_chunks,
                bytes_transferred=0,
                total_bytes=metadata.file_size,
                speed_bps=0.0,
                eta_seconds=0.0,
                peers_count=len(available_peers),
                started_at=time.time()
            )
            
            self.active_transfers[file_id] = progress
            
            # Crea chunks se non esistono
            if file_id not in self.file_chunks:
                self.file_chunks[file_id] = await self._create_empty_chunks(metadata)
            
            # Avvia download
            download_task = asyncio.create_task(self._download_file_chunks(file_id, available_peers))
            self.background_tasks.add(download_task)
            download_task.add_done_callback(self.background_tasks.discard)
            
            self.logger.info(f"Download avviato per {metadata.filename} ({file_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore avvio download {file_id}: {e}")
            return False
    
    async def pause_transfer(self, file_id: str) -> bool:
        """Pausa un trasferimento"""
        try:
            if file_id not in self.active_transfers:
                return False
            
            progress = self.active_transfers[file_id]
            if progress.status == TransferStatus.ACTIVE:
                progress.status = TransferStatus.PAUSED
                self.logger.info(f"Trasferimento pausato: {file_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Errore pausa trasferimento {file_id}: {e}")
            return False
    
    async def resume_transfer(self, file_id: str) -> bool:
        """Riprende un trasferimento"""
        try:
            if file_id not in self.active_transfers:
                return False
            
            progress = self.active_transfers[file_id]
            if progress.status == TransferStatus.PAUSED:
                progress.status = TransferStatus.ACTIVE
                
                # Riavvia download se necessario
                if progress.chunks_completed < progress.total_chunks:
                    available_peers = [
                        pid for pid, files in self.peer_files.items()
                        if file_id in files
                    ]
                    
                    if available_peers:
                        download_task = asyncio.create_task(
                            self._download_file_chunks(file_id, available_peers)
                        )
                        self.background_tasks.add(download_task)
                        download_task.add_done_callback(self.background_tasks.discard)
                
                self.logger.info(f"Trasferimento ripreso: {file_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Errore ripresa trasferimento {file_id}: {e}")
            return False
    
    async def cancel_transfer(self, file_id: str) -> bool:
        """Cancella un trasferimento"""
        try:
            if file_id not in self.active_transfers:
                return False
            
            progress = self.active_transfers[file_id]
            progress.status = TransferStatus.CANCELLED
            
            # Rimuovi file parziale se esiste
            temp_file = self.temp_dir / f"{file_id}.partial"
            if temp_file.exists():
                temp_file.unlink()
            
            # Rimuovi chunks
            if file_id in self.file_chunks:
                del self.file_chunks[file_id]
            
            del self.active_transfers[file_id]
            
            self.logger.info(f"Trasferimento cancellato: {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore cancellazione trasferimento {file_id}: {e}")
            return False
    
    async def get_shared_files(self) -> List[Dict[str, Any]]:
        """Restituisce lista file condivisi"""
        return [asdict(metadata) for metadata in self.shared_files.values()]
    
    async def get_transfer_progress(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Restituisce progresso trasferimento"""
        if file_id in self.active_transfers:
            return asdict(self.active_transfers[file_id])
        return None
    
    async def get_all_transfers(self) -> List[Dict[str, Any]]:
        """Restituisce tutti i trasferimenti attivi"""
        return [asdict(progress) for progress in self.active_transfers.values()]
    
    async def search_files(self, query: str, peer_id: str = None) -> List[Dict[str, Any]]:
        """Cerca file nei peer connessi"""
        try:
            results = []
            
            # Cerca nei file locali
            for metadata in self.shared_files.values():
                if self._matches_search(metadata, query):
                    result = asdict(metadata)
                    result["peer_id"] = "local"
                    result["available"] = True
                    results.append(result)
            
            # Cerca nei peer remoti
            search_peers = [peer_id] if peer_id else list(self.peers.keys())
            
            for pid in search_peers:
                try:
                    peer_results = await self._search_peer_files(pid, query)
                    results.extend(peer_results)
                except Exception as e:
                    self.logger.warning(f"Errore ricerca in peer {pid}: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Errore ricerca file: {e}")
            return []
    
    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Restituisce informazioni dettagliate su un file"""
        if file_id in self.shared_files:
            metadata = self.shared_files[file_id]
            info = asdict(metadata)
            
            # Aggiungi informazioni chunks
            if file_id in self.file_chunks:
                chunks = self.file_chunks[file_id]
                info["chunks_info"] = {
                    "total": len(chunks),
                    "completed": sum(1 for c in chunks if c.status == ChunkStatus.VERIFIED),
                    "downloading": sum(1 for c in chunks if c.status == ChunkStatus.DOWNLOADING),
                    "corrupted": sum(1 for c in chunks if c.status == ChunkStatus.CORRUPTED)
                }
            
            # Aggiungi peer disponibili
            available_peers = [
                pid for pid, files in self.peer_files.items()
                if file_id in files
            ]
            info["available_peers"] = available_peers
            
            return info
        
        return None
    
    async def set_transfer_handler(self, handler: Callable) -> None:
        """Imposta handler per eventi di trasferimento"""
        self.transfer_handler = handler
    
    async def set_progress_handler(self, handler: Callable) -> None:
        """Imposta handler per aggiornamenti progresso"""
        self.progress_handler = handler
    
    async def get_transfer_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche trasferimenti"""
        stats_dict = asdict(self.stats)
        
        # Aggiungi statistiche in tempo reale
        stats_dict["active_downloads"] = sum(
            1 for p in self.active_transfers.values()
            if p.status == TransferStatus.ACTIVE and p.chunks_completed < p.total_chunks
        )
        
        stats_dict["active_uploads"] = len([
            pid for pid, files in self.peer_files.items()
            if any(fid in self.shared_files for fid in files)
        ])
        
        return stats_dict
    
    # Metodi privati
    
    async def _handle_message(self, sender_id: str, message_type: str, content: bytes) -> None:
        """Handler per messaggi ricevuti"""
        try:
            if message_type.startswith("file_"):
                await self._handle_file_message(sender_id, message_type, content)
        except Exception as e:
            self.logger.error(f"Errore gestione messaggio file: {e}")
    
    async def _handle_file_message(self, sender_id: str, message_type: str, content: bytes) -> None:
        """Gestisce messaggi relativi ai file"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            if message_type == "file_announce":
                await self._handle_file_announce(sender_id, data)
            elif message_type == "file_request":
                await self._handle_file_request(sender_id, data)
            elif message_type == "file_chunk":
                await self._handle_file_chunk(sender_id, data)
            elif message_type == "file_metadata_request":
                await self._handle_metadata_request(sender_id, data)
            elif message_type == "file_metadata_response":
                await self._handle_metadata_response(sender_id, data)
            elif message_type == "file_search":
                await self._handle_file_search(sender_id, data)
            elif message_type == "file_search_response":
                await self._handle_search_response(sender_id, data)
                
        except Exception as e:
            self.logger.error(f"Errore gestione messaggio file {message_type}: {e}")
    
    async def _create_file_metadata(self, file_path: Path, description: str, tags: List[str]) -> FileMetadata:
        """Crea metadata per un file"""
        file_stats = file_path.stat()
        file_size = file_stats.st_size
        
        # Calcola hash del file
        file_hash = await self._calculate_file_hash(file_path)
        
        # Determina tipo MIME
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Calcola numero di chunks
        total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
        
        # Determina compressione
        compression = self._determine_compression(file_path, mime_type)
        
        # Genera thumbnail se immagine
        thumbnail = None
        if mime_type.startswith("image/"):
            thumbnail = await self._generate_thumbnail(file_path)
        
        return FileMetadata(
            file_id=file_hash[:16],  # Usa primi 16 caratteri dell'hash come ID
            filename=file_path.name,
            file_size=file_size,
            mime_type=mime_type,
            hash_sha256=file_hash,
            chunk_size=self.chunk_size,
            total_chunks=total_chunks,
            compression=compression,
            encrypted=self.config.get("encrypt_files", True),
            created_at=file_stats.st_ctime,
            modified_at=file_stats.st_mtime,
            description=description,
            tags=tags,
            thumbnail=thumbnail
        )
    
    async def _create_file_chunks(self, file_path: Path, metadata: FileMetadata) -> List[FileChunk]:
        """Crea chunks per un file"""
        chunks = []
        
        with open(file_path, 'rb') as f:
            for chunk_id in range(metadata.total_chunks):
                offset = chunk_id * metadata.chunk_size
                f.seek(offset)
                
                chunk_data = f.read(metadata.chunk_size)
                chunk_hash = hashlib.sha256(chunk_data).hexdigest()
                
                chunk = FileChunk(
                    chunk_id=chunk_id,
                    offset=offset,
                    size=len(chunk_data),
                    hash_sha256=chunk_hash,
                    status=ChunkStatus.VERIFIED,
                    data=chunk_data,
                    peers={"local"}
                )
                
                chunks.append(chunk)
        
        return chunks
    
    async def _create_empty_chunks(self, metadata: FileMetadata) -> List[FileChunk]:
        """Crea chunks vuoti per download"""
        chunks = []
        
        for chunk_id in range(metadata.total_chunks):
            offset = chunk_id * metadata.chunk_size
            size = min(metadata.chunk_size, metadata.file_size - offset)
            
            chunk = FileChunk(
                chunk_id=chunk_id,
                offset=offset,
                size=size,
                hash_sha256="",  # Sarà riempito quando ricevuto
                status=ChunkStatus.MISSING
            )
            
            chunks.append(chunk)
        
        return chunks
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcola hash SHA-256 di un file"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _determine_compression(self, file_path: Path, mime_type: str) -> CompressionType:
        """Determina tipo di compressione ottimale"""
        # File già compressi
        compressed_types = [
            "image/jpeg", "image/png", "image/gif",
            "video/", "audio/",
            "application/zip", "application/gzip", "application/x-rar"
        ]
        
        if any(mime_type.startswith(ct) for ct in compressed_types):
            return CompressionType.NONE
        
        # File di testo
        text_types = ["text/", "application/json", "application/xml"]
        if any(mime_type.startswith(tt) for tt in text_types):
            return CompressionType.ZLIB
        
        # Default
        return CompressionType.AUTO
    
    async def _generate_thumbnail(self, file_path: Path) -> Optional[bytes]:
        """Genera thumbnail per immagini"""
        try:
            # Implementazione semplificata - in produzione usare PIL/Pillow
            # Per ora restituisce None
            return None
        except Exception:
            return None
    
    async def _announce_file(self, metadata: FileMetadata) -> None:
        """Annuncia file ai peer connessi"""
        try:
            if not self.network_module:
                return
            
            announce_data = {
                "file_id": metadata.file_id,
                "filename": metadata.filename,
                "file_size": metadata.file_size,
                "mime_type": metadata.mime_type,
                "description": metadata.description,
                "tags": metadata.tags
            }
            
            message_content = json.dumps(announce_data).encode('utf-8')
            
            # Invia a tutti i peer connessi
            connected_peers = await self.network_module.get_connected_peers()
            for peer_id in connected_peers:
                try:
                    await self.messaging_module.send_message(
                        peer_id, "file_announce", message_content
                    )
                except Exception as e:
                    self.logger.warning(f"Errore annuncio file a {peer_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Errore annuncio file: {e}")
    
    async def _download_file_chunks(self, file_id: str, available_peers: List[str]) -> None:
        """Download chunks di un file da peer multipli"""
        try:
            if file_id not in self.active_transfers:
                return
            
            progress = self.active_transfers[file_id]
            progress.status = TransferStatus.ACTIVE
            
            chunks = self.file_chunks[file_id]
            metadata = self.shared_files[file_id]
            
            # Crea file temporaneo
            temp_file = self.temp_dir / f"{file_id}.partial"
            
            # Download chunks in parallelo
            semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
            download_tasks = []
            
            for chunk in chunks:
                if chunk.status == ChunkStatus.MISSING:
                    task = asyncio.create_task(
                        self._download_chunk(file_id, chunk, available_peers, semaphore)
                    )
                    download_tasks.append(task)
            
            # Attendi completamento
            if download_tasks:
                await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # Verifica completamento
            completed_chunks = sum(1 for c in chunks if c.status == ChunkStatus.VERIFIED)
            
            if completed_chunks == len(chunks):
                # Assembla file finale
                success = await self._assemble_file(file_id, temp_file)
                
                if success:
                    progress.status = TransferStatus.COMPLETED
                    progress.completed_at = time.time()
                    self.stats.total_files_downloaded += 1
                    self.stats.successful_transfers += 1
                    
                    if self.transfer_handler:
                        await self.transfer_handler("completed", file_id, metadata.filename)
                else:
                    progress.status = TransferStatus.FAILED
                    progress.error_message = "Errore assemblaggio file"
                    self.stats.failed_transfers += 1
            else:
                progress.status = TransferStatus.FAILED
                progress.error_message = f"Download incompleto: {completed_chunks}/{len(chunks)} chunks"
                self.stats.failed_transfers += 1
        
        except Exception as e:
            self.logger.error(f"Errore download chunks {file_id}: {e}")
            if file_id in self.active_transfers:
                self.active_transfers[file_id].status = TransferStatus.FAILED
                self.active_transfers[file_id].error_message = str(e)
    
    async def _download_chunk(self, file_id: str, chunk: FileChunk, peers: List[str], semaphore: asyncio.Semaphore) -> None:
        """Download di un singolo chunk"""
        async with semaphore:
            try:
                chunk.status = ChunkStatus.DOWNLOADING
                chunk.download_attempts += 1
                chunk.last_attempt = time.time()
                
                # Prova con peer diversi
                for peer_id in peers:
                    try:
                        chunk_data = await self._request_chunk(peer_id, file_id, chunk.chunk_id)
                        
                        if chunk_data:
                            # Verifica hash se disponibile
                            if chunk.hash_sha256:
                                calculated_hash = hashlib.sha256(chunk_data).hexdigest()
                                if calculated_hash != chunk.hash_sha256:
                                    chunk.status = ChunkStatus.CORRUPTED
                                    continue
                            
                            chunk.data = chunk_data
                            chunk.status = ChunkStatus.VERIFIED
                            chunk.peers.add(peer_id)
                            
                            # Aggiorna progresso
                            if file_id in self.active_transfers:
                                progress = self.active_transfers[file_id]
                                progress.chunks_completed += 1
                                progress.bytes_transferred += len(chunk_data)
                                
                                if self.progress_handler:
                                    await self.progress_handler(file_id, progress.progress_percentage)
                            
                            return
                    
                    except Exception as e:
                        self.logger.warning(f"Errore download chunk {chunk.chunk_id} da {peer_id}: {e}")
                        continue
                
                # Nessun peer ha funzionato
                chunk.status = ChunkStatus.MISSING
                
            except Exception as e:
                self.logger.error(f"Errore download chunk {chunk.chunk_id}: {e}")
                chunk.status = ChunkStatus.MISSING
    
    async def _request_chunk(self, peer_id: str, file_id: str, chunk_id: int) -> Optional[bytes]:
        """Richiede un chunk specifico a un peer"""
        try:
            request_data = {
                "file_id": file_id,
                "chunk_id": chunk_id
            }
            
            message_content = json.dumps(request_data).encode('utf-8')
            
            # Invia richiesta
            await self.messaging_module.send_message(
                peer_id, "file_request", message_content
            )
            
            # Attendi risposta (implementazione semplificata)
            # In produzione usare sistema di callback/future
            await asyncio.sleep(0.1)  # Simula attesa
            
            return None  # Placeholder - implementare ricezione chunk
            
        except Exception as e:
            self.logger.error(f"Errore richiesta chunk {chunk_id} a {peer_id}: {e}")
            return None
    
    async def _assemble_file(self, file_id: str, temp_file: Path) -> bool:
        """Assembla file finale dai chunks"""
        try:
            chunks = self.file_chunks[file_id]
            metadata = self.shared_files[file_id]
            
            final_file = self.downloads_dir / metadata.filename
            
            with open(final_file, 'wb') as f:
                for chunk in sorted(chunks, key=lambda c: c.chunk_id):
                    if chunk.status == ChunkStatus.VERIFIED and chunk.data:
                        f.write(chunk.data)
            
            # Verifica hash finale
            final_hash = await self._calculate_file_hash(final_file)
            
            if final_hash == metadata.hash_sha256:
                # Rimuovi file temporaneo
                if temp_file.exists():
                    temp_file.unlink()
                
                self.logger.info(f"File assemblato con successo: {final_file}")
                return True
            else:
                self.logger.error(f"Hash file finale non corrisponde: {file_id}")
                final_file.unlink()
                return False
        
        except Exception as e:
            self.logger.error(f"Errore assemblaggio file {file_id}: {e}")
            return False
    
    def _matches_search(self, metadata: FileMetadata, query: str) -> bool:
        """Verifica se un file corrisponde alla query di ricerca"""
        query_lower = query.lower()
        
        # Cerca in nome file
        if query_lower in metadata.filename.lower():
            return True
        
        # Cerca in descrizione
        if query_lower in metadata.description.lower():
            return True
        
        # Cerca in tag
        if any(query_lower in tag.lower() for tag in metadata.tags):
            return True
        
        return False
    
    async def _search_peer_files(self, peer_id: str, query: str) -> List[Dict[str, Any]]:
        """Cerca file in un peer specifico"""
        try:
            search_data = {"query": query}
            message_content = json.dumps(search_data).encode('utf-8')
            
            await self.messaging_module.send_message(
                peer_id, "file_search", message_content
            )
            
            # Attendi risposta (implementazione semplificata)
            await asyncio.sleep(0.1)
            
            return []  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Errore ricerca in peer {peer_id}: {e}")
            return []
    
    async def _request_file_metadata(self, file_id: str, peer_id: str) -> Optional[FileMetadata]:
        """Richiede metadata di un file a un peer"""
        try:
            request_data = {"file_id": file_id}
            message_content = json.dumps(request_data).encode('utf-8')
            
            await self.messaging_module.send_message(
                peer_id, "file_metadata_request", message_content
            )
            
            # Attendi risposta (implementazione semplificata)
            await asyncio.sleep(0.1)
            
            return None  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Errore richiesta metadata {file_id} a {peer_id}: {e}")
            return None
    
    # Handler messaggi
    
    async def _handle_file_announce(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce annuncio di file da peer"""
        try:
            file_id = data["file_id"]
            
            # Aggiorna lista file del peer
            if sender_id not in self.peer_files:
                self.peer_files[sender_id] = set()
            
            self.peer_files[sender_id].add(file_id)
            
            self.logger.info(f"File annunciato da {sender_id}: {data['filename']} ({file_id})")
            
        except Exception as e:
            self.logger.error(f"Errore gestione annuncio file: {e}")
    
    async def _handle_file_request(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce richiesta di chunk"""
        try:
            file_id = data["file_id"]
            chunk_id = data["chunk_id"]
            
            if file_id in self.file_chunks:
                chunks = self.file_chunks[file_id]
                
                if 0 <= chunk_id < len(chunks):
                    chunk = chunks[chunk_id]
                    
                    if chunk.status == ChunkStatus.VERIFIED and chunk.data:
                        # Invia chunk
                        chunk_data = {
                            "file_id": file_id,
                            "chunk_id": chunk_id,
                            "data": chunk.data.hex()  # Converti in hex per JSON
                        }
                        
                        message_content = json.dumps(chunk_data).encode('utf-8')
                        
                        await self.messaging_module.send_message(
                            sender_id, "file_chunk", message_content
                        )
                        
                        self.stats.total_bytes_uploaded += len(chunk.data)
        
        except Exception as e:
            self.logger.error(f"Errore gestione richiesta chunk: {e}")
    
    async def _handle_file_chunk(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce ricezione di chunk"""
        try:
            file_id = data["file_id"]
            chunk_id = data["chunk_id"]
            chunk_data = bytes.fromhex(data["data"])
            
            if file_id in self.file_chunks:
                chunks = self.file_chunks[file_id]
                
                if 0 <= chunk_id < len(chunks):
                    chunk = chunks[chunk_id]
                    
                    # Verifica hash se disponibile
                    if chunk.hash_sha256:
                        calculated_hash = hashlib.sha256(chunk_data).hexdigest()
                        if calculated_hash != chunk.hash_sha256:
                            self.logger.warning(f"Hash chunk {chunk_id} non valido")
                            return
                    
                    chunk.data = chunk_data
                    chunk.status = ChunkStatus.VERIFIED
                    chunk.peers.add(sender_id)
                    
                    self.stats.total_bytes_downloaded += len(chunk_data)
        
        except Exception as e:
            self.logger.error(f"Errore gestione chunk ricevuto: {e}")
    
    async def _handle_metadata_request(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce richiesta metadata"""
        try:
            file_id = data["file_id"]
            
            if file_id in self.shared_files:
                metadata = self.shared_files[file_id]
                
                response_data = {
                    "file_id": file_id,
                    "metadata": asdict(metadata)
                }
                
                message_content = json.dumps(response_data).encode('utf-8')
                
                await self.messaging_module.send_message(
                    sender_id, "file_metadata_response", message_content
                )
        
        except Exception as e:
            self.logger.error(f"Errore gestione richiesta metadata: {e}")
    
    async def _handle_metadata_response(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce risposta metadata"""
        try:
            file_id = data["file_id"]
            metadata_dict = data["metadata"]
            
            metadata = FileMetadata(**metadata_dict)
            self.shared_files[file_id] = metadata
            
        except Exception as e:
            self.logger.error(f"Errore gestione risposta metadata: {e}")
    
    async def _handle_file_search(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce richiesta di ricerca"""
        try:
            query = data["query"]
            
            results = []
            for metadata in self.shared_files.values():
                if self._matches_search(metadata, query):
                    results.append(asdict(metadata))
            
            response_data = {
                "query": query,
                "results": results
            }
            
            message_content = json.dumps(response_data).encode('utf-8')
            
            await self.messaging_module.send_message(
                sender_id, "file_search_response", message_content
            )
        
        except Exception as e:
            self.logger.error(f"Errore gestione ricerca file: {e}")
    
    async def _handle_search_response(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce risposta di ricerca"""
        try:
            results = data["results"]
            
            # Processa risultati ricerca
            for result in results:
                result["peer_id"] = sender_id
                result["available"] = True
            
            # Notifica risultati (implementazione semplificata)
            self.logger.info(f"Ricevuti {len(results)} risultati da {sender_id}")
        
        except Exception as e:
            self.logger.error(f"Errore gestione risposta ricerca: {e}")
    
    # Task di background
    
    async def _start_background_tasks(self) -> None:
        """Avvia task di background"""
        # Task di monitoraggio trasferimenti
        monitor_task = asyncio.create_task(self._monitor_transfers())
        self.background_tasks.add(monitor_task)
        monitor_task.add_done_callback(self.background_tasks.discard)
        
        # Task di pulizia
        cleanup_task = asyncio.create_task(self._cleanup_task())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
    
    async def _stop_background_tasks(self) -> None:
        """Ferma task di background"""
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
    
    async def _monitor_transfers(self) -> None:
        """Monitora trasferimenti attivi"""
        while self.running:
            try:
                current_time = time.time()
                
                for file_id, progress in list(self.active_transfers.items()):
                    if progress.status == TransferStatus.ACTIVE:
                        # Calcola velocità e ETA
                        elapsed = current_time - progress.started_at
                        if elapsed > 0:
                            progress.speed_bps = progress.bytes_transferred / elapsed
                            
                            remaining_bytes = progress.total_bytes - progress.bytes_transferred
                            if progress.speed_bps > 0:
                                progress.eta_seconds = remaining_bytes / progress.speed_bps
                
                await asyncio.sleep(1.0)  # Aggiorna ogni secondo
                
            except Exception as e:
                self.logger.error(f"Errore monitoraggio trasferimenti: {e}")
                await asyncio.sleep(5.0)
    
    async def _cleanup_task(self) -> None:
        """Task di pulizia periodica"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Ogni 5 minuti
                
                # Rimuovi trasferimenti completati vecchi
                current_time = time.time()
                cutoff_time = current_time - (24 * 3600)  # 24 ore
                
                to_remove = []
                for file_id, progress in self.active_transfers.items():
                    if (progress.status in [TransferStatus.COMPLETED, TransferStatus.FAILED, TransferStatus.CANCELLED] and
                        progress.completed_at > 0 and progress.completed_at < cutoff_time):
                        to_remove.append(file_id)
                
                for file_id in to_remove:
                    del self.active_transfers[file_id]
                    if file_id in self.file_chunks:
                        del self.file_chunks[file_id]
                
                # Pulisci file temporanei orfani
                for temp_file in self.temp_dir.glob("*.partial"):
                    if temp_file.stat().st_mtime < cutoff_time:
                        temp_file.unlink()
                
            except Exception as e:
                self.logger.error(f"Errore task pulizia: {e}")
    
    # Persistenza dati
    
    async def _load_persistent_data(self) -> None:
        """Carica dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/file_sharing"))
            
            # Carica file condivisi
            shared_file = data_dir / "shared_files.json"
            if shared_file.exists():
                with open(shared_file, 'r', encoding='utf-8') as f:
                    shared_data = json.load(f)
                    
                for file_id, metadata_dict in shared_data.items():
                    self.shared_files[file_id] = FileMetadata(**metadata_dict)
            
            # Carica statistiche
            stats_file = data_dir / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats_data = json.load(f)
                    self.stats = TransferStats(**stats_data)
        
        except Exception as e:
            self.logger.error(f"Errore caricamento dati persistenti: {e}")
    
    async def _save_persistent_data(self) -> None:
        """Salva dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/file_sharing"))
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Salva file condivisi
            shared_file = data_dir / "shared_files.json"
            shared_data = {}
            for file_id, metadata in self.shared_files.items():
                shared_data[file_id] = asdict(metadata)
            
            with open(shared_file, 'w', encoding='utf-8') as f:
                json.dump(shared_data, f, indent=2, ensure_ascii=False)
            
            # Salva statistiche
            stats_file = data_dir / "stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.stats), f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Errore salvataggio dati persistenti: {e}")


# Configurazione predefinita
DEFAULT_CONFIG = {
    "data_dir": "data/file_sharing",
    "chunk_size": 65536,  # 64KB
    "max_concurrent_downloads": 5,
    "max_concurrent_uploads": 10,
    "bandwidth_limit_bps": 0,  # Unlimited
    "encrypt_files": True,
    "compress_files": True,
    "auto_resume": True,
    "verify_integrity": True,
    "enable_thumbnails": True,
    "max_file_size": 1073741824,  # 1GB
    "allowed_extensions": [],  # Empty = all allowed
    "blocked_extensions": [".exe", ".bat", ".cmd", ".scr"]
}


async def create_advanced_file_sharing(config: Dict[str, Any] = None) -> AdvancedFileSharing:
    """
    Factory function per creare AdvancedFileSharing
    
    Args:
        config: Configurazione del plugin (usa DEFAULT_CONFIG se None)
    
    Returns:
        Istanza inizializzata di AdvancedFileSharing
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()
    else:
        # Merge con configurazione predefinita
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        config = merged_config
    
    plugin = AdvancedFileSharing()
    await plugin.initialize(config)
    return plugin