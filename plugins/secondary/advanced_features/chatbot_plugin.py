"""
ChatBot Plugin - Plugin Secondario per LaboonChat2

Plugin intelligente che fornisce:
- Assistente AI conversazionale
- Comandi automatici e shortcuts
- Risposte contestuali
- Integrazione con moduli core
- Apprendimento dalle conversazioni
- Personalizzazione comportamento
"""

import asyncio
import json
import time
import re
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from laboon_chat2.core.interfaces import ISecondaryPlugin


class BotPersonality(Enum):
    """Personalità del bot"""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    TECHNICAL = "technical"
    CASUAL = "casual"


class ResponseType(Enum):
    """Tipi di risposta"""
    DIRECT = "direct"
    COMMAND = "command"
    HELP = "help"
    INFORMATION = "information"
    ENTERTAINMENT = "entertainment"
    ERROR = "error"


@dataclass
class BotCommand:
    """Comando del bot"""
    name: str
    pattern: str
    description: str
    usage: str
    category: str = "general"
    requires_args: bool = False
    admin_only: bool = False
    cooldown: float = 0.0
    last_used: float = 0.0
    
    def can_execute(self, is_admin: bool = False) -> bool:
        """Verifica se il comando può essere eseguito"""
        if self.admin_only and not is_admin:
            return False
        
        if self.cooldown > 0:
            if time.time() - self.last_used < self.cooldown:
                return False
        
        return True


@dataclass
class BotResponse:
    """Risposta del bot"""
    content: str
    response_type: ResponseType
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ConversationContext:
    """Contesto conversazione"""
    user_id: str
    last_messages: List[str]
    topics: List[str]
    preferences: Dict[str, Any]
    session_start: float
    message_count: int = 0
    
    def __post_init__(self):
        if not self.last_messages:
            self.last_messages = []
        if not self.topics:
            self.topics = []
        if not self.preferences:
            self.preferences = {}
        if self.session_start == 0:
            self.session_start = time.time()


@dataclass
class BotStats:
    """Statistiche del bot"""
    total_messages: int = 0
    commands_executed: int = 0
    conversations_started: int = 0
    average_response_time: float = 0.0
    most_used_commands: Dict[str, int] = None
    user_interactions: Dict[str, int] = None
    uptime: float = 0.0
    
    def __post_init__(self):
        if self.most_used_commands is None:
            self.most_used_commands = {}
        if self.user_interactions is None:
            self.user_interactions = {}


class ChatBotPlugin(ISecondaryPlugin):
    """
    Plugin ChatBot intelligente per LaboonChat2
    
    Fornisce assistenza AI conversazionale con:
    - Comandi automatici
    - Risposte contestuali
    - Apprendimento adattivo
    - Personalizzazione
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.commands: Dict[str, BotCommand] = {}
        self.contexts: Dict[str, ConversationContext] = {}
        self.stats = BotStats()
        self.personality = BotPersonality.FRIENDLY
        
        # Moduli core
        self.security_module = None
        self.messaging_module = None
        self.network_module = None
        self.interface_module = None
        
        # Handler eventi
        self.message_handler: Optional[Callable] = None
        
        # Stato interno
        self.running = False
        self.bot_id = "laboon_chatbot"
        self.logger = logging.getLogger(__name__)
        
        # Risposte predefinite
        self.responses = {
            "greetings": [
                "Ciao! Come posso aiutarti oggi?",
                "Salve! Sono qui per assisterti.",
                "Benvenuto! Cosa posso fare per te?",
                "Ciao! Pronto ad aiutarti con LaboonChat2!"
            ],
            "help": [
                "Ecco cosa posso fare per te:",
                "I miei comandi disponibili sono:",
                "Posso aiutarti con questi comandi:"
            ],
            "unknown": [
                "Non ho capito. Puoi ripetere?",
                "Comando non riconosciuto. Digita /help per aiuto.",
                "Scusa, non conosco questo comando.",
                "Prova con /help per vedere i comandi disponibili."
            ],
            "error": [
                "Ops! Si è verificato un errore.",
                "Qualcosa è andato storto. Riprova.",
                "Errore nell'esecuzione. Controlla i parametri."
            ]
        }
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Inizializza il plugin"""
        self.config = config.copy()
        
        # Configura personalità
        personality_str = config.get("personality", "friendly")
        try:
            self.personality = BotPersonality(personality_str)
        except ValueError:
            self.personality = BotPersonality.FRIENDLY
        
        # Crea directory dati
        data_dir = Path(config.get("data_dir", "data/chatbot"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Carica dati persistenti
        await self._load_persistent_data()
        
        # Inizializza comandi
        await self._initialize_commands()
        
        # Carica risposte personalizzate
        await self._load_custom_responses()
        
        self.running = True
        self.stats.uptime = time.time()
        
        self.logger.info(f"ChatBotPlugin inizializzato - Personalità: {self.personality.value}")
    
    async def cleanup(self) -> None:
        """Pulisce le risorse del plugin"""
        self.running = False
        
        # Salva dati persistenti
        await self._save_persistent_data()
        
        self.logger.info("ChatBotPlugin terminato")
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul plugin"""
        return {
            "name": "ChatBotPlugin",
            "version": "1.0.0",
            "type": "secondary",
            "category": "advanced_features",
            "description": "Assistente AI conversazionale con comandi automatici e risposte intelligenti",
            "author": "LaboonChat2 Team",
            "capabilities": [
                "ai_conversation",
                "automatic_commands",
                "contextual_responses",
                "user_learning",
                "personality_customization",
                "help_system"
            ],
            "dependencies": ["messaging", "security"],
            "optional_dependencies": ["network", "interface"]
        }
    
    async def activate(self) -> bool:
        """Attiva il plugin"""
        try:
            # Registra handler messaggi
            if self.messaging_module:
                await self.messaging_module.set_message_handler(self._handle_message)
            
            self.logger.info("ChatBotPlugin attivato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore attivazione ChatBotPlugin: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Disattiva il plugin"""
        try:
            # Rimuovi handler messaggi
            if self.messaging_module:
                await self.messaging_module.set_message_handler(None)
            
            self.logger.info("ChatBotPlugin disattivato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore disattivazione ChatBotPlugin: {e}")
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
            "personality": self.personality.value,
            "total_commands": len(self.commands),
            "active_conversations": len(self.contexts),
            "stats": asdict(self.stats)
        }
    
    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Aggiorna configurazione del plugin"""
        self.config.update(new_config)
        
        # Aggiorna personalità se cambiata
        if "personality" in new_config:
            try:
                self.personality = BotPersonality(new_config["personality"])
            except ValueError:
                pass
    
    # Metodi specifici del ChatBot
    
    async def process_message(self, user_id: str, message: str) -> Optional[BotResponse]:
        """Processa messaggio e genera risposta"""
        try:
            start_time = time.time()
            
            # Aggiorna contesto conversazione
            context = await self._get_or_create_context(user_id)
            context.last_messages.append(message)
            context.message_count += 1
            
            # Mantieni solo ultimi 10 messaggi
            if len(context.last_messages) > 10:
                context.last_messages = context.last_messages[-10:]
            
            # Verifica se è un comando
            if message.startswith('/'):
                response = await self._process_command(user_id, message, context)
            else:
                response = await self._process_conversation(user_id, message, context)
            
            # Aggiorna statistiche
            response_time = time.time() - start_time
            self.stats.total_messages += 1
            
            if self.stats.average_response_time == 0:
                self.stats.average_response_time = response_time
            else:
                self.stats.average_response_time = (
                    self.stats.average_response_time * 0.9 + response_time * 0.1
                )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Errore processamento messaggio: {e}")
            return BotResponse(
                content=random.choice(self.responses["error"]),
                response_type=ResponseType.ERROR
            )
    
    async def add_custom_command(self, command: BotCommand) -> bool:
        """Aggiunge comando personalizzato"""
        try:
            self.commands[command.name] = command
            await self._save_commands()
            return True
        except Exception as e:
            self.logger.error(f"Errore aggiunta comando {command.name}: {e}")
            return False
    
    async def remove_command(self, command_name: str) -> bool:
        """Rimuove comando"""
        try:
            if command_name in self.commands:
                del self.commands[command_name]
                await self._save_commands()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Errore rimozione comando {command_name}: {e}")
            return False
    
    async def get_conversation_history(self, user_id: str) -> List[str]:
        """Restituisce cronologia conversazione"""
        if user_id in self.contexts:
            return self.contexts[user_id].last_messages.copy()
        return []
    
    async def clear_conversation(self, user_id: str) -> bool:
        """Pulisce conversazione utente"""
        try:
            if user_id in self.contexts:
                self.contexts[user_id].last_messages.clear()
                self.contexts[user_id].topics.clear()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Errore pulizia conversazione {user_id}: {e}")
            return False
    
    async def set_user_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Imposta preferenza utente"""
        try:
            context = await self._get_or_create_context(user_id)
            context.preferences[key] = value
            await self._save_contexts()
            return True
        except Exception as e:
            self.logger.error(f"Errore impostazione preferenza {key} per {user_id}: {e}")
            return False
    
    async def get_bot_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche dettagliate"""
        stats_dict = asdict(self.stats)
        stats_dict["uptime_hours"] = (time.time() - self.stats.uptime) / 3600
        stats_dict["commands_available"] = len(self.commands)
        stats_dict["active_users"] = len(self.contexts)
        return stats_dict
    
    # Metodi privati
    
    async def _handle_message(self, sender_id: str, message_type: str, content: bytes) -> None:
        """Handler per messaggi ricevuti"""
        try:
            if message_type == "text_message":
                message_text = content.decode('utf-8')
                
                # Verifica se il messaggio è diretto al bot
                if self._is_bot_mention(message_text):
                    # Rimuovi menzione bot
                    clean_message = self._clean_bot_mention(message_text)
                    
                    # Processa messaggio
                    response = await self.process_message(sender_id, clean_message)
                    
                    if response and self.messaging_module:
                        # Invia risposta
                        response_content = response.content.encode('utf-8')
                        await self.messaging_module.send_message(
                            sender_id, "text_message", response_content
                        )
        
        except Exception as e:
            self.logger.error(f"Errore gestione messaggio: {e}")
    
    def _is_bot_mention(self, message: str) -> bool:
        """Verifica se il messaggio menziona il bot"""
        message_lower = message.lower()
        mentions = [
            f"@{self.bot_id}",
            "bot",
            "chatbot",
            "laboon",
            "aiuto",
            "help"
        ]
        
        return any(mention in message_lower for mention in mentions)
    
    def _clean_bot_mention(self, message: str) -> str:
        """Rimuove menzioni bot dal messaggio"""
        # Rimuovi @bot_id
        message = re.sub(f"@{self.bot_id}", "", message, flags=re.IGNORECASE)
        
        # Rimuovi altre menzioni comuni
        message = re.sub(r"\b(bot|chatbot|laboon)\b", "", message, flags=re.IGNORECASE)
        
        return message.strip()
    
    async def _get_or_create_context(self, user_id: str) -> ConversationContext:
        """Ottiene o crea contesto conversazione"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(
                user_id=user_id,
                last_messages=[],
                topics=[],
                preferences={},
                session_start=time.time()
            )
            self.stats.conversations_started += 1
        
        return self.contexts[user_id]
    
    async def _process_command(self, user_id: str, message: str, context: ConversationContext) -> BotResponse:
        """Processa comando"""
        # Estrai comando e argomenti
        parts = message[1:].split()
        command_name = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        # Verifica se comando esiste
        if command_name not in self.commands:
            return BotResponse(
                content=f"Comando '/{command_name}' non riconosciuto. Usa /help per vedere i comandi disponibili.",
                response_type=ResponseType.ERROR
            )
        
        command = self.commands[command_name]
        
        # Verifica permessi e cooldown
        is_admin = context.preferences.get("is_admin", False)
        if not command.can_execute(is_admin):
            if command.admin_only:
                return BotResponse(
                    content="Comando riservato agli amministratori.",
                    response_type=ResponseType.ERROR
                )
            else:
                cooldown_remaining = command.cooldown - (time.time() - command.last_used)
                return BotResponse(
                    content=f"Comando in cooldown. Riprova tra {cooldown_remaining:.1f} secondi.",
                    response_type=ResponseType.ERROR
                )
        
        # Verifica argomenti
        if command.requires_args and not args:
            return BotResponse(
                content=f"Comando richiede argomenti. Uso: {command.usage}",
                response_type=ResponseType.ERROR
            )
        
        # Esegui comando
        try:
            response = await self._execute_command(command_name, args, user_id, context)
            command.last_used = time.time()
            self.stats.commands_executed += 1
            
            # Aggiorna statistiche comando
            if command_name not in self.stats.most_used_commands:
                self.stats.most_used_commands[command_name] = 0
            self.stats.most_used_commands[command_name] += 1
            
            return response
            
        except Exception as e:
            self.logger.error(f"Errore esecuzione comando {command_name}: {e}")
            return BotResponse(
                content=f"Errore esecuzione comando: {str(e)}",
                response_type=ResponseType.ERROR
            )
    
    async def _execute_command(self, command_name: str, args: List[str], user_id: str, context: ConversationContext) -> BotResponse:
        """Esegue comando specifico"""
        if command_name == "help":
            return await self._cmd_help(args)
        elif command_name == "status":
            return await self._cmd_status(args)
        elif command_name == "stats":
            return await self._cmd_stats(args)
        elif command_name == "clear":
            return await self._cmd_clear(user_id)
        elif command_name == "personality":
            return await self._cmd_personality(args, user_id)
        elif command_name == "preferences":
            return await self._cmd_preferences(args, user_id)
        elif command_name == "network":
            return await self._cmd_network(args)
        elif command_name == "peers":
            return await self._cmd_peers(args)
        elif command_name == "time":
            return await self._cmd_time(args)
        elif command_name == "joke":
            return await self._cmd_joke(args)
        else:
            return BotResponse(
                content=f"Comando {command_name} non implementato.",
                response_type=ResponseType.ERROR
            )
    
    async def _process_conversation(self, user_id: str, message: str, context: ConversationContext) -> BotResponse:
        """Processa conversazione normale"""
        message_lower = message.lower()
        
        # Saluti
        if any(greeting in message_lower for greeting in ["ciao", "salve", "buongiorno", "buonasera", "hello", "hi"]):
            response_text = random.choice(self.responses["greetings"])
            return BotResponse(
                content=response_text,
                response_type=ResponseType.DIRECT
            )
        
        # Richieste di aiuto
        if any(help_word in message_lower for help_word in ["aiuto", "help", "comandi", "cosa puoi fare"]):
            return await self._cmd_help([])
        
        # Domande su stato
        if any(status_word in message_lower for status_word in ["come stai", "stato", "status", "come va"]):
            return await self._cmd_status([])
        
        # Conversazione generica basata su personalità
        return await self._generate_personality_response(message, context)
    
    async def _generate_personality_response(self, message: str, context: ConversationContext) -> BotResponse:
        """Genera risposta basata su personalità"""
        responses_by_personality = {
            BotPersonality.FRIENDLY: [
                "Interessante! Dimmi di più.",
                "Capisco quello che dici. È un argomento affascinante!",
                "Grazie per aver condiviso questo con me.",
                "Mi piace parlare di queste cose con te!"
            ],
            BotPersonality.PROFESSIONAL: [
                "Ho preso nota della tua osservazione.",
                "Questo è un punto valido da considerare.",
                "Posso fornirti informazioni aggiuntive se necessario.",
                "La tua richiesta è stata registrata."
            ],
            BotPersonality.HUMOROUS: [
                "Haha, interessante! Come un computer che cerca di essere divertente! 😄",
                "Quello che dici mi ricorda una barzelletta... ma non la ricordo! 😅",
                "Sono d'accordo! Anche se sono solo un bot, ho i miei gusti! 🤖",
                "Ottima osservazione! I miei circuiti sono d'accordo! ⚡"
            ],
            BotPersonality.TECHNICAL: [
                "Analizzando il tuo input, posso fornire le seguenti informazioni...",
                "Dal punto di vista tecnico, questo è un argomento complesso.",
                "I dati suggeriscono che la tua osservazione è corretta.",
                "Processando la tua richiesta attraverso i miei algoritmi..."
            ],
            BotPersonality.CASUAL: [
                "Sì, capisco! È proprio così.",
                "Mmm, interessante quello che dici.",
                "Ok, ci sta! Cosa ne pensi tu?",
                "Ah sì, ho sentito parlare di questa cosa."
            ]
        }
        
        responses = responses_by_personality.get(self.personality, responses_by_personality[BotPersonality.FRIENDLY])
        response_text = random.choice(responses)
        
        return BotResponse(
            content=response_text,
            response_type=ResponseType.DIRECT,
            confidence=0.7
        )
    
    async def _initialize_commands(self) -> None:
        """Inizializza comandi predefiniti"""
        default_commands = [
            BotCommand(
                name="help",
                pattern=r"/help\s*(\w+)?",
                description="Mostra aiuto generale o per comando specifico",
                usage="/help [comando]",
                category="general"
            ),
            BotCommand(
                name="status",
                pattern=r"/status",
                description="Mostra stato del bot e del sistema",
                usage="/status",
                category="general"
            ),
            BotCommand(
                name="stats",
                pattern=r"/stats",
                description="Mostra statistiche dettagliate",
                usage="/stats",
                category="general"
            ),
            BotCommand(
                name="clear",
                pattern=r"/clear",
                description="Pulisce cronologia conversazione",
                usage="/clear",
                category="general"
            ),
            BotCommand(
                name="personality",
                pattern=r"/personality\s+(\w+)",
                description="Cambia personalità del bot",
                usage="/personality [friendly|professional|humorous|technical|casual]",
                category="settings",
                requires_args=True
            ),
            BotCommand(
                name="preferences",
                pattern=r"/preferences\s+(\w+)\s+(.+)",
                description="Gestisce preferenze utente",
                usage="/preferences [get|set|list] [chiave] [valore]",
                category="settings"
            ),
            BotCommand(
                name="network",
                pattern=r"/network",
                description="Mostra informazioni di rete",
                usage="/network",
                category="system"
            ),
            BotCommand(
                name="peers",
                pattern=r"/peers",
                description="Mostra peer connessi",
                usage="/peers",
                category="system"
            ),
            BotCommand(
                name="time",
                pattern=r"/time",
                description="Mostra data e ora corrente",
                usage="/time",
                category="utility"
            ),
            BotCommand(
                name="joke",
                pattern=r"/joke",
                description="Racconta una barzelletta",
                usage="/joke",
                category="entertainment",
                cooldown=10.0
            )
        ]
        
        for command in default_commands:
            self.commands[command.name] = command
    
    # Implementazione comandi
    
    async def _cmd_help(self, args: List[str]) -> BotResponse:
        """Comando help"""
        if args and args[0] in self.commands:
            # Aiuto per comando specifico
            command = self.commands[args[0]]
            content = f"**/{command.name}**\n"
            content += f"Descrizione: {command.description}\n"
            content += f"Uso: {command.usage}\n"
            content += f"Categoria: {command.category}"
            
            if command.admin_only:
                content += "\n⚠️ Solo amministratori"
            if command.cooldown > 0:
                content += f"\n⏱️ Cooldown: {command.cooldown}s"
        else:
            # Aiuto generale
            content = random.choice(self.responses["help"]) + "\n\n"
            
            categories = {}
            for cmd in self.commands.values():
                if cmd.category not in categories:
                    categories[cmd.category] = []
                categories[cmd.category].append(cmd)
            
            for category, commands in categories.items():
                content += f"**{category.title()}:**\n"
                for cmd in commands:
                    content += f"  /{cmd.name} - {cmd.description}\n"
                content += "\n"
            
            content += "Usa `/help [comando]` per dettagli specifici."
        
        return BotResponse(
            content=content,
            response_type=ResponseType.HELP
        )
    
    async def _cmd_status(self, args: List[str]) -> BotResponse:
        """Comando status"""
        uptime_hours = (time.time() - self.stats.uptime) / 3600
        
        content = f"🤖 **ChatBot Status**\n"
        content += f"Personalità: {self.personality.value}\n"
        content += f"Uptime: {uptime_hours:.1f} ore\n"
        content += f"Messaggi processati: {self.stats.total_messages}\n"
        content += f"Comandi eseguiti: {self.stats.commands_executed}\n"
        content += f"Conversazioni attive: {len(self.contexts)}\n"
        content += f"Tempo risposta medio: {self.stats.average_response_time:.3f}s"
        
        return BotResponse(
            content=content,
            response_type=ResponseType.INFORMATION
        )
    
    async def _cmd_stats(self, args: List[str]) -> BotResponse:
        """Comando stats"""
        stats = await self.get_bot_stats()
        
        content = f"📊 **Statistiche Dettagliate**\n"
        content += f"Uptime: {stats['uptime_hours']:.1f} ore\n"
        content += f"Messaggi totali: {stats['total_messages']}\n"
        content += f"Comandi eseguiti: {stats['commands_executed']}\n"
        content += f"Conversazioni iniziate: {stats['conversations_started']}\n"
        content += f"Utenti attivi: {stats['active_users']}\n"
        content += f"Comandi disponibili: {stats['commands_available']}\n"
        
        if stats['most_used_commands']:
            content += "\n**Comandi più usati:**\n"
            sorted_commands = sorted(
                stats['most_used_commands'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for cmd, count in sorted_commands:
                content += f"  /{cmd}: {count} volte\n"
        
        return BotResponse(
            content=content,
            response_type=ResponseType.INFORMATION
        )
    
    async def _cmd_clear(self, user_id: str) -> BotResponse:
        """Comando clear"""
        success = await self.clear_conversation(user_id)
        
        if success:
            content = "✅ Cronologia conversazione pulita!"
        else:
            content = "❌ Errore pulizia cronologia."
        
        return BotResponse(
            content=content,
            response_type=ResponseType.COMMAND
        )
    
    async def _cmd_personality(self, args: List[str], user_id: str) -> BotResponse:
        """Comando personality"""
        if not args:
            content = f"Personalità attuale: **{self.personality.value}**\n"
            content += "Personalità disponibili: friendly, professional, humorous, technical, casual"
            return BotResponse(content=content, response_type=ResponseType.INFORMATION)
        
        new_personality = args[0].lower()
        try:
            self.personality = BotPersonality(new_personality)
            content = f"✅ Personalità cambiata in: **{self.personality.value}**"
        except ValueError:
            content = "❌ Personalità non valida. Usa: friendly, professional, humorous, technical, casual"
        
        return BotResponse(
            content=content,
            response_type=ResponseType.COMMAND
        )
    
    async def _cmd_preferences(self, args: List[str], user_id: str) -> BotResponse:
        """Comando preferences"""
        context = await self._get_or_create_context(user_id)
        
        if not args:
            # Lista preferenze
            if context.preferences:
                content = "**Le tue preferenze:**\n"
                for key, value in context.preferences.items():
                    content += f"  {key}: {value}\n"
            else:
                content = "Nessuna preferenza impostata."
        elif args[0] == "set" and len(args) >= 3:
            # Imposta preferenza
            key = args[1]
            value = " ".join(args[2:])
            context.preferences[key] = value
            content = f"✅ Preferenza '{key}' impostata a '{value}'"
        elif args[0] == "get" and len(args) >= 2:
            # Ottieni preferenza
            key = args[1]
            value = context.preferences.get(key, "Non impostata")
            content = f"**{key}:** {value}"
        else:
            content = "Uso: /preferences [get|set|list] [chiave] [valore]"
        
        return BotResponse(
            content=content,
            response_type=ResponseType.COMMAND
        )
    
    async def _cmd_network(self, args: List[str]) -> BotResponse:
        """Comando network"""
        if not self.network_module:
            content = "❌ Modulo network non disponibile."
        else:
            try:
                stats = await self.network_module.get_network_stats()
                content = f"🌐 **Stato Rete**\n"
                content += f"Peer connessi: {stats['connected_peers']}\n"
                content += f"Connessioni attive: {stats['active_connections']}\n"
                content += f"Latenza media: {stats['average_latency']:.3f}s\n"
                content += f"Qualità rete: {stats['network_quality']:.2f}\n"
                content += f"Messaggi inviati: {stats['total_messages_sent']}\n"
                content += f"Messaggi ricevuti: {stats['total_messages_received']}"
            except Exception as e:
                content = f"❌ Errore lettura stato rete: {e}"
        
        return BotResponse(
            content=content,
            response_type=ResponseType.INFORMATION
        )
    
    async def _cmd_peers(self, args: List[str]) -> BotResponse:
        """Comando peers"""
        if not self.network_module:
            content = "❌ Modulo network non disponibile."
        else:
            try:
                peers = await self.network_module.get_connected_peers()
                if peers:
                    content = f"👥 **Peer Connessi ({len(peers)}):**\n"
                    for peer_id in peers:
                        peer_info = await self.network_module.get_peer_info(peer_id)
                        if peer_info:
                            content += f"  • {peer_id} ({peer_info['address']}:{peer_info['port']})\n"
                        else:
                            content += f"  • {peer_id}\n"
                else:
                    content = "Nessun peer connesso."
            except Exception as e:
                content = f"❌ Errore lettura peer: {e}"
        
        return BotResponse(
            content=content,
            response_type=ResponseType.INFORMATION
        )
    
    async def _cmd_time(self, args: List[str]) -> BotResponse:
        """Comando time"""
        import datetime
        now = datetime.datetime.now()
        content = f"🕐 **Data e Ora**\n"
        content += f"Data: {now.strftime('%d/%m/%Y')}\n"
        content += f"Ora: {now.strftime('%H:%M:%S')}\n"
        content += f"Timestamp: {int(now.timestamp())}"
        
        return BotResponse(
            content=content,
            response_type=ResponseType.INFORMATION
        )
    
    async def _cmd_joke(self, args: List[str]) -> BotResponse:
        """Comando joke"""
        jokes = [
            "Perché i programmatori preferiscono il buio? Perché la luce attira i bug! 🐛",
            "Cosa dice un bit quando incontra un byte? 'Ciao, come va? Io sto a 1!' 💾",
            "Perché i robot non hanno paura? Perché hanno nervi d'acciaio! 🤖",
            "Come si chiama un computer che canta? Un Dell! 🎵",
            "Perché i computer non si ammalano mai? Perché hanno un buon antivirus! 💊",
            "Cosa fa un hacker quando ha fame? Fa un byte! 🍔",
            "Perché i programmatori odiano la natura? Troppi bug! 🌿🐛",
            "Come si chiama un algoritmo che balla? Un algo-ritmo! 💃"
        ]
        
        joke = random.choice(jokes)
        
        return BotResponse(
            content=joke,
            response_type=ResponseType.ENTERTAINMENT
        )
    
    # Persistenza dati
    
    async def _load_persistent_data(self) -> None:
        """Carica dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/chatbot"))
            
            # Carica contesti
            contexts_file = data_dir / "contexts.json"
            if contexts_file.exists():
                with open(contexts_file, 'r', encoding='utf-8') as f:
                    contexts_data = json.load(f)
                    
                for user_id, context_data in contexts_data.items():
                    self.contexts[user_id] = ConversationContext(**context_data)
            
            # Carica statistiche
            stats_file = data_dir / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats_data = json.load(f)
                    self.stats = BotStats(**stats_data)
        
        except Exception as e:
            self.logger.error(f"Errore caricamento dati persistenti: {e}")
    
    async def _save_persistent_data(self) -> None:
        """Salva dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/chatbot"))
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Salva contesti (solo ultimi 7 giorni)
            contexts_file = data_dir / "contexts.json"
            recent_contexts = {}
            cutoff_time = time.time() - (7 * 24 * 3600)  # 7 giorni
            
            for user_id, context in self.contexts.items():
                if context.session_start > cutoff_time:
                    recent_contexts[user_id] = asdict(context)
            
            with open(contexts_file, 'w', encoding='utf-8') as f:
                json.dump(recent_contexts, f, indent=2, ensure_ascii=False)
            
            # Salva statistiche
            stats_file = data_dir / "stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.stats), f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Errore salvataggio dati persistenti: {e}")
    
    async def _save_commands(self) -> None:
        """Salva comandi personalizzati"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/chatbot"))
            data_dir.mkdir(parents=True, exist_ok=True)
            
            commands_file = data_dir / "custom_commands.json"
            commands_data = {}
            
            for name, command in self.commands.items():
                commands_data[name] = asdict(command)
            
            with open(commands_file, 'w', encoding='utf-8') as f:
                json.dump(commands_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self.logger.error(f"Errore salvataggio comandi: {e}")
    
    async def _save_contexts(self) -> None:
        """Salva contesti conversazioni"""
        await self._save_persistent_data()
    
    async def _load_custom_responses(self) -> None:
        """Carica risposte personalizzate"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/chatbot"))
            responses_file = data_dir / "custom_responses.json"
            
            if responses_file.exists():
                with open(responses_file, 'r', encoding='utf-8') as f:
                    custom_responses = json.load(f)
                    
                # Merge con risposte predefinite
                for category, responses in custom_responses.items():
                    if category in self.responses:
                        self.responses[category].extend(responses)
                    else:
                        self.responses[category] = responses
        
        except Exception as e:
            self.logger.error(f"Errore caricamento risposte personalizzate: {e}")


# Configurazione predefinita
DEFAULT_CONFIG = {
    "personality": "friendly",
    "data_dir": "data/chatbot",
    "enable_learning": True,
    "max_context_messages": 10,
    "response_delay": 0.5,
    "enable_commands": True,
    "enable_jokes": True,
    "admin_users": [],
    "banned_words": [],
    "auto_respond": True,
    "mention_required": False
}


async def create_chatbot_plugin(config: Dict[str, Any] = None) -> ChatBotPlugin:
    """
    Factory function per creare ChatBotPlugin
    
    Args:
        config: Configurazione del plugin (usa DEFAULT_CONFIG se None)
    
    Returns:
        Istanza inizializzata di ChatBotPlugin
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()
    else:
        # Merge con configurazione predefinita
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        config = merged_config
    
    plugin = ChatBotPlugin()
    await plugin.initialize(config)
    return plugin