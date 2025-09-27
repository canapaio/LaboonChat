"""
Sistema di Configurazione Dinamica per Plugin LaboonChat
Basato sui pattern della comunità open source per auto-generazione UI da schema JSON.

Ispirato da:
- Pydantic per validazione e schema JSON
- UI-Schema per auto-generazione interfacce
- Electron-Python per architetture ibride
- Visual JSON Editor per GUI da schema
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Type, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import jsonschema
from datetime import datetime

# Configurazione logging
logger = logging.getLogger(__name__)

class ConfigFieldType(Enum):
    """Tipi di campo supportati per le configurazioni plugin."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    COLOR = "color"
    PASSWORD = "password"

@dataclass
class ConfigField:
    """Definizione di un campo di configurazione."""
    name: str
    field_type: ConfigFieldType
    title: str
    description: str
    default: Any = None
    required: bool = False
    enum_values: Optional[List[str]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    ui_widget: Optional[str] = None  # Per personalizzazioni UI specifiche
    group: Optional[str] = None  # Per raggruppare campi nell'UI
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Converte il campo in schema JSON."""
        # Gestione speciale per ENUM
        if self.field_type == ConfigFieldType.ENUM:
            schema = {
                "type": "string",
                "title": self.title,
                "description": self.description
            }
            if self.enum_values:
                schema["enum"] = self.enum_values
        else:
            schema = {
                "type": self.field_type.value,
                "title": self.title,
                "description": self.description
            }
        
        if self.default is not None:
            schema["default"] = self.default
            
        if self.min_value is not None:
            schema["minimum"] = self.min_value
            
        if self.max_value is not None:
            schema["maximum"] = self.max_value
            
        if self.pattern:
            schema["pattern"] = self.pattern
            
        # Estensioni UI personalizzate
        if self.ui_widget:
            schema["ui:widget"] = self.ui_widget
            
        if self.group:
            schema["ui:group"] = self.group
            
        # Gestione tipi speciali
        if self.field_type == ConfigFieldType.FILE_PATH:
            schema["format"] = "file-path"
            schema["ui:widget"] = "file"
        elif self.field_type == ConfigFieldType.DIRECTORY_PATH:
            schema["format"] = "directory-path"
            schema["ui:widget"] = "directory"
        elif self.field_type == ConfigFieldType.COLOR:
            schema["format"] = "color"
            schema["ui:widget"] = "color"
        elif self.field_type == ConfigFieldType.PASSWORD:
            schema["ui:widget"] = "password"
            
        return schema

@dataclass
class PluginConfigSchema:
    """Schema di configurazione per un plugin."""
    plugin_id: str
    plugin_name: str
    version: str
    description: str
    fields: List[ConfigField] = field(default_factory=list)
    groups: Dict[str, str] = field(default_factory=dict)  # group_id -> group_title
    
    def add_field(self, field: ConfigField) -> None:
        """Aggiunge un campo allo schema."""
        self.fields.append(field)
        
    def add_group(self, group_id: str, group_title: str) -> None:
        """Aggiunge un gruppo per organizzare i campi."""
        self.groups[group_id] = group_title
        
    def to_json_schema(self) -> Dict[str, Any]:
        """Genera lo schema JSON completo."""
        properties = {}
        required = []
        
        for field in self.fields:
            properties[field.name] = field.to_json_schema()
            if field.required:
                required.append(field.name)
                
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": f"Configurazione {self.plugin_name}",
            "description": self.description,
            "properties": properties,
            "additionalProperties": False
        }
        
        if required:
            schema["required"] = required
            
        # Metadati per l'UI
        schema["ui:meta"] = {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "version": self.version,
            "groups": self.groups
        }
        
        return schema
        
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Valida una configurazione contro lo schema."""
        try:
            jsonschema.validate(config, self.to_json_schema())
            return True, []
        except jsonschema.ValidationError as e:
            return False, [str(e)]

class PluginConfigManager:
    """Gestore centralizzato delle configurazioni plugin."""
    
    def __init__(self, config_dir: str = "plugin_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.schemas_dir = self.config_dir / "schemas"
        self.schemas_dir.mkdir(exist_ok=True)
        
        self.configs_dir = self.config_dir / "configs"
        self.configs_dir.mkdir(exist_ok=True)
        
        self.ui_cache_dir = self.config_dir / "ui_cache"
        self.ui_cache_dir.mkdir(exist_ok=True)
        
        self._schemas: Dict[str, PluginConfigSchema] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"PluginConfigManager inizializzato in: {self.config_dir}")
        
    def has_plugin(self, plugin_id: str) -> bool:
        """Verifica se un plugin è registrato."""
        return plugin_id in self._schemas
        
    def validate_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Valida una configurazione per un plugin specifico."""
        if plugin_id not in self._schemas:
            logger.error(f"Schema non trovato per plugin: {plugin_id}")
            return False
            
        schema = self._schemas[plugin_id]
        is_valid, errors = schema.validate_config(config)
        
        if not is_valid:
            logger.error(f"Configurazione non valida per {plugin_id}: {errors}")
            
        return is_valid
        
    def register_plugin_schema(self, schema: PluginConfigSchema) -> None:
        """Registra lo schema di configurazione di un plugin."""
        self._schemas[schema.plugin_id] = schema
        
        # Salva lo schema JSON
        schema_file = self.schemas_dir / f"{schema.plugin_id}.schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema.to_json_schema(), f, indent=2, ensure_ascii=False)
            
        # Genera l'UI cache
        self._generate_ui_metadata(schema)
        
        logger.info(f"Schema registrato per plugin: {schema.plugin_id}")
        
    def _generate_ui_metadata(self, schema: PluginConfigSchema) -> None:
        """Genera metadati per l'auto-generazione dell'UI."""
        ui_metadata = {
            "plugin_id": schema.plugin_id,
            "plugin_name": schema.plugin_name,
            "version": schema.version,
            "description": schema.description,
            "generated_at": datetime.now().isoformat(),
            "groups": [],
            "fields": []
        }
        
        # Organizza i campi per gruppi
        grouped_fields = {}
        ungrouped_fields = []
        
        for field in schema.fields:
            if field.group:
                if field.group not in grouped_fields:
                    grouped_fields[field.group] = []
                grouped_fields[field.group].append(field)
            else:
                ungrouped_fields.append(field)
                
        # Aggiungi gruppi
        for group_id, group_title in schema.groups.items():
            if group_id in grouped_fields:
                group_metadata = {
                    "id": group_id,
                    "title": group_title,
                    "fields": [self._field_to_ui_metadata(f) for f in grouped_fields[group_id]]
                }
                ui_metadata["groups"].append(group_metadata)
                
        # Aggiungi campi non raggruppati
        if ungrouped_fields:
            ui_metadata["fields"] = [self._field_to_ui_metadata(f) for f in ungrouped_fields]
            
        # Salva metadati UI
        ui_file = self.ui_cache_dir / f"{schema.plugin_id}.ui.json"
        with open(ui_file, 'w', encoding='utf-8') as f:
            json.dump(ui_metadata, f, indent=2, ensure_ascii=False)
            
    def _field_to_ui_metadata(self, field: ConfigField) -> Dict[str, Any]:
        """Converte un campo in metadati UI."""
        return {
            "name": field.name,
            "type": field.field_type.value,
            "title": field.title,
            "description": field.description,
            "default": field.default,
            "required": field.required,
            "widget": field.ui_widget,
            "enum_values": field.enum_values,
            "min_value": field.min_value,
            "max_value": field.max_value,
            "pattern": field.pattern
        }
        
    def load_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """Carica la configurazione di un plugin."""
        if plugin_id in self._configs:
            return self._configs[plugin_id].copy()
            
        config_file = self.configs_dir / f"{plugin_id}.config.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            # Genera configurazione di default dallo schema
            config = self._generate_default_config(plugin_id)
            
        self._configs[plugin_id] = config
        return config.copy()
        
    def save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Salva la configurazione di un plugin."""
        if plugin_id not in self._schemas:
            logger.error(f"Schema non trovato per plugin: {plugin_id}")
            return False
            
        # Valida la configurazione
        schema = self._schemas[plugin_id]
        is_valid, errors = schema.validate_config(config)
        
        if not is_valid:
            logger.error(f"Configurazione non valida per {plugin_id}: {errors}")
            return False
            
        # Salva la configurazione
        config_file = self.configs_dir / f"{plugin_id}.config.json"
        
        # Backup della configurazione precedente
        if config_file.exists():
            backup_file = self.configs_dir / f"{plugin_id}.config.backup.json"
            config_file.rename(backup_file)
            
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        self._configs[plugin_id] = config.copy()
        logger.info(f"Configurazione salvata per plugin: {plugin_id}")
        return True
        
    def _generate_default_config(self, plugin_id: str) -> Dict[str, Any]:
        """Genera una configurazione di default dallo schema."""
        if plugin_id not in self._schemas:
            return {}
            
        schema = self._schemas[plugin_id]
        config = {}
        
        for field in schema.fields:
            if field.default is not None:
                config[field.name] = field.default
            elif field.required:
                # Valori di default per tipi richiesti
                if field.field_type == ConfigFieldType.STRING:
                    config[field.name] = ""
                elif field.field_type == ConfigFieldType.INTEGER:
                    config[field.name] = 0
                elif field.field_type == ConfigFieldType.FLOAT:
                    config[field.name] = 0.0
                elif field.field_type == ConfigFieldType.BOOLEAN:
                    config[field.name] = False
                elif field.field_type == ConfigFieldType.ARRAY:
                    config[field.name] = []
                elif field.field_type == ConfigFieldType.OBJECT:
                    config[field.name] = {}
                    
        return config
        
    def get_plugin_schema(self, plugin_id: str) -> Optional[PluginConfigSchema]:
        """Ottiene lo schema di un plugin."""
        return self._schemas.get(plugin_id)
        
    def get_ui_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Ottiene i metadati UI per un plugin."""
        ui_file = self.ui_cache_dir / f"{plugin_id}.ui.json"
        
        if ui_file.exists():
            with open(ui_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
        
    def list_plugins(self) -> List[str]:
        """Lista tutti i plugin registrati."""
        return list(self._schemas.keys())
        
    def export_plugin_config(self, plugin_id: str, export_path: str) -> bool:
        """Esporta la configurazione di un plugin."""
        try:
            config = self.load_plugin_config(plugin_id)
            schema = self.get_plugin_schema(plugin_id)
            
            export_data = {
                "plugin_id": plugin_id,
                "plugin_name": schema.plugin_name if schema else plugin_id,
                "version": schema.version if schema else "unknown",
                "exported_at": datetime.now().isoformat(),
                "config": config
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Configurazione esportata: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Errore nell'esportazione: {e}")
            return False
            
    def import_plugin_config(self, import_path: str) -> bool:
        """Importa la configurazione di un plugin."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            plugin_id = import_data["plugin_id"]
            config = import_data["config"]
            
            return self.save_plugin_config(plugin_id, config)
        except Exception as e:
            logger.error(f"Errore nell'importazione: {e}")
            return False

# Istanza globale del gestore configurazioni
config_manager = PluginConfigManager()

def get_config_manager() -> PluginConfigManager:
    """Ottiene l'istanza globale del gestore configurazioni."""
    return config_manager