"""
Generatore Automatico di Interfacce di Configurazione
Basato sui pattern UI-Schema e Visual JSON Editor per auto-generazione UI da schema JSON.

Genera interfacce web responsive per la configurazione dei plugin.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

try:
    from .plugin_config_system import PluginConfigManager, ConfigFieldType
except ImportError:
    from plugin_config_system import PluginConfigManager, ConfigFieldType

logger = logging.getLogger(__name__)

class ConfigUIGenerator:
    """Generatore di interfacce utente per configurazioni plugin."""
    
    def __init__(self, config_manager: PluginConfigManager):
        self.config_manager = config_manager
        self.templates_dir = Path(__file__).parent / "ui_templates"
        self.templates_dir.mkdir(exist_ok=True)
        self.output_dir = Path("generated_ui")
        self.output_dir.mkdir(exist_ok=True)
        
        # Inizializza i template di base
        self._create_base_templates()
        
    def _create_base_templates(self) -> None:
        """Crea i template di base per l'UI."""
        
        # Template HTML principale
        main_template = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configurazione Plugin - {{plugin_name}}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .config-container {
            max-width: 800px;
            margin: 2rem auto;
            padding: 2rem;
        }
        .field-group {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border-left: 4px solid #007bff;
        }
        .field-item {
            margin-bottom: 1rem;
        }
        .field-description {
            font-size: 0.875rem;
            color: #6c757d;
            margin-top: 0.25rem;
        }
        .config-header {
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        .btn-save {
            background: #28a745;
            border: none;
            padding: 0.75rem 2rem;
            font-weight: 500;
        }
        .btn-reset {
            background: #6c757d;
            border: none;
            padding: 0.75rem 2rem;
            font-weight: 500;
        }
        .validation-error {
            color: #dc3545;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        .color-preview {
            width: 40px;
            height: 40px;
            border-radius: 4px;
            border: 2px solid #dee2e6;
            display: inline-block;
            margin-left: 0.5rem;
            vertical-align: middle;
        }
    </style>
</head>
<body>
    <div class="config-container">
        <div class="config-header">
            <h1><i class="bi bi-gear-fill"></i> {{plugin_name}}</h1>
            <p class="mb-0">{{description}}</p>
            <small>Versione: {{version}}</small>
        </div>
        
        <form id="configForm">
            {{content}}
            
            <div class="d-flex gap-2 mt-4">
                <button type="submit" class="btn btn-save text-white">
                    <i class="bi bi-check-circle"></i> Salva Configurazione
                </button>
                <button type="button" class="btn btn-reset text-white" onclick="resetForm()">
                    <i class="bi bi-arrow-clockwise"></i> Ripristina
                </button>
                <button type="button" class="btn btn-outline-primary" onclick="exportConfig()">
                    <i class="bi bi-download"></i> Esporta
                </button>
                <button type="button" class="btn btn-outline-secondary" onclick="importConfig()">
                    <i class="bi bi-upload"></i> Importa
                </button>
            </div>
        </form>
    </div>
    
    <input type="file" id="importFile" accept=".json" style="display: none;" onchange="handleImport(event)">
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const pluginId = '{{plugin_id}}';
        const originalConfig = {{original_config}};
        let currentConfig = JSON.parse(JSON.stringify(originalConfig));
        
        {{javascript_code}}
    </script>
</body>
</html>"""
        
        # Salva il template principale
        with open(self.templates_dir / "main_template.html", 'w', encoding='utf-8') as f:
            f.write(main_template)
            
        # Template JavaScript
        js_template = """
        // Gestione form configurazione
        document.getElementById('configForm').addEventListener('submit', function(e) {
            e.preventDefault();
            saveConfiguration();
        });
        
        function saveConfiguration() {
            const formData = new FormData(document.getElementById('configForm'));
            const config = {};
            
            // Raccogli tutti i valori del form
            for (let [key, value] of formData.entries()) {
                const field = getFieldMetadata(key);
                if (field) {
                    config[key] = convertValue(value, field.type);
                }
            }
            
            // Valida la configurazione
            if (validateConfiguration(config)) {
                // Invia al backend (implementare chiamata API)
                console.log('Configurazione da salvare:', config);
                showNotification('Configurazione salvata con successo!', 'success');
                currentConfig = JSON.parse(JSON.stringify(config));
            }
        }
        
        function convertValue(value, type) {
            switch (type) {
                case 'integer':
                    return parseInt(value) || 0;
                case 'number':
                    return parseFloat(value) || 0.0;
                case 'boolean':
                    return value === 'true' || value === true;
                case 'array':
                    try {
                        return JSON.parse(value);
                    } catch {
                        return value.split(',').map(s => s.trim()).filter(s => s);
                    }
                default:
                    return value;
            }
        }
        
        function validateConfiguration(config) {
            // Implementare validazione basata su schema
            return true;
        }
        
        function resetForm() {
            if (confirm('Sei sicuro di voler ripristinare la configurazione originale?')) {
                loadConfiguration(originalConfig);
                showNotification('Configurazione ripristinata', 'info');
            }
        }
        
        function loadConfiguration(config) {
            for (let [key, value] of Object.entries(config)) {
                const element = document.getElementById(key);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = value;
                    } else if (element.type === 'color') {
                        element.value = value;
                        updateColorPreview(key, value);
                    } else {
                        element.value = Array.isArray(value) ? JSON.stringify(value) : value;
                    }
                }
            }
        }
        
        function exportConfig() {
            const config = getCurrentConfig();
            const blob = new Blob([JSON.stringify(config, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${pluginId}_config.json`;
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function importConfig() {
            document.getElementById('importFile').click();
        }
        
        function handleImport(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    try {
                        const config = JSON.parse(e.target.result);
                        loadConfiguration(config);
                        showNotification('Configurazione importata con successo!', 'success');
                    } catch (error) {
                        showNotification('Errore nel file di configurazione', 'error');
                    }
                };
                reader.readAsText(file);
            }
        }
        
        function getCurrentConfig() {
            const formData = new FormData(document.getElementById('configForm'));
            const config = {};
            for (let [key, value] of formData.entries()) {
                const field = getFieldMetadata(key);
                if (field) {
                    config[key] = convertValue(value, field.type);
                }
            }
            return config;
        }
        
        function getFieldMetadata(fieldName) {
            // Implementare lookup metadati campo
            return {type: 'string'};
        }
        
        function updateColorPreview(fieldName, color) {
            const preview = document.getElementById(fieldName + '_preview');
            if (preview) {
                preview.style.backgroundColor = color;
            }
        }
        
        function showNotification(message, type) {
            // Implementare sistema notifiche
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
        
        // Carica configurazione iniziale
        document.addEventListener('DOMContentLoaded', function() {
            loadConfiguration(currentConfig);
        });
        """
        
        with open(self.templates_dir / "config_script.js", 'w', encoding='utf-8') as f:
            f.write(js_template)
            
    def generate_plugin_ui(self, plugin_id: str) -> Optional[str]:
        """Genera l'interfaccia UI per un plugin specifico."""
        try:
            # Ottieni metadati UI
            ui_metadata = self.config_manager.get_ui_metadata(plugin_id)
            if not ui_metadata:
                logger.error(f"Metadati UI non trovati per plugin: {plugin_id}")
                return None
                
            # Ottieni configurazione corrente
            current_config = self.config_manager.load_plugin_config(plugin_id)
            
            # Genera contenuto HTML
            content_html = self._generate_form_content(ui_metadata)
            
            # Carica template principale
            with open(self.templates_dir / "main_template.html", 'r', encoding='utf-8') as f:
                template = f.read()
                
            # Carica JavaScript
            with open(self.templates_dir / "config_script.js", 'r', encoding='utf-8') as f:
                javascript_code = f.read()
                
            # Sostituisci placeholder
            html_content = template.replace('{{plugin_name}}', ui_metadata['plugin_name'])
            html_content = html_content.replace('{{plugin_id}}', plugin_id)
            html_content = html_content.replace('{{description}}', ui_metadata['description'])
            html_content = html_content.replace('{{version}}', ui_metadata['version'])
            html_content = html_content.replace('{{content}}', content_html)
            html_content = html_content.replace('{{original_config}}', json.dumps(current_config))
            html_content = html_content.replace('{{javascript_code}}', javascript_code)
            
            # Salva file generato
            output_file = self.output_dir / f"{plugin_id}_config.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"UI generata per plugin {plugin_id}: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Errore nella generazione UI per {plugin_id}: {e}")
            return None
            
    def _generate_form_content(self, ui_metadata: Dict[str, Any]) -> str:
        """Genera il contenuto del form basato sui metadati UI."""
        content_parts = []
        
        # Campi raggruppati
        for group in ui_metadata.get('groups', []):
            group_html = f"""
            <div class="field-group">
                <h4><i class="bi bi-folder"></i> {group['title']}</h4>
                {self._generate_fields_html(group['fields'])}
            </div>
            """
            content_parts.append(group_html)
            
        # Campi non raggruppati
        ungrouped_fields = ui_metadata.get('fields', [])
        if ungrouped_fields:
            content_parts.append(self._generate_fields_html(ungrouped_fields))
            
        return '\n'.join(content_parts)
        
    def _generate_fields_html(self, fields: List[Dict[str, Any]]) -> str:
        """Genera HTML per una lista di campi."""
        fields_html = []
        
        for field in fields:
            field_html = self._generate_field_html(field)
            fields_html.append(f'<div class="field-item">{field_html}</div>')
            
        return '\n'.join(fields_html)
        
    def _generate_field_html(self, field: Dict[str, Any]) -> str:
        """Genera HTML per un singolo campo."""
        field_name = field['name']
        field_type = field['type']
        field_title = field['title']
        field_description = field.get('description', '')
        required = field.get('required', False)
        widget = field.get('widget')
        
        # Label
        label_html = f"""
        <label for="{field_name}" class="form-label">
            {field_title}
            {' <span class="text-danger">*</span>' if required else ''}
        </label>
        """
        
        # Input field
        input_html = self._generate_input_html(field)
        
        # Description
        description_html = f'<div class="field-description">{field_description}</div>' if field_description else ''
        
        return f"""
        {label_html}
        {input_html}
        {description_html}
        """
        
    def _generate_input_html(self, field: Dict[str, Any]) -> str:
        """Genera HTML per l'input di un campo."""
        field_name = field['name']
        field_type = field['type']
        widget = field.get('widget')
        required = field.get('required', False)
        
        base_attrs = f'id="{field_name}" name="{field_name}" class="form-control"'
        if required:
            base_attrs += ' required'
            
        if field_type == 'boolean':
            return f"""
            <div class="form-check">
                <input type="checkbox" {base_attrs.replace('form-control', 'form-check-input')}>
                <label class="form-check-label" for="{field_name}">Attiva</label>
            </div>
            """
            
        elif field_type == 'integer':
            min_val = field.get('min_value', '')
            max_val = field.get('max_value', '')
            return f'<input type="number" {base_attrs} min="{min_val}" max="{max_val}" step="1">'
            
        elif field_type == 'number':
            min_val = field.get('min_value', '')
            max_val = field.get('max_value', '')
            return f'<input type="number" {base_attrs} min="{min_val}" max="{max_val}" step="0.01">'
            
        elif field_type == 'enum':
            options = field.get('enum_values', [])
            options_html = '\n'.join([f'<option value="{opt}">{opt}</option>' for opt in options])
            return f'<select {base_attrs}>\n{options_html}\n</select>'
            
        elif widget == 'color':
            return f"""
            <div class="d-flex align-items-center">
                <input type="color" {base_attrs.replace('form-control', 'form-control-color')} onchange="updateColorPreview('{field_name}', this.value)">
                <div id="{field_name}_preview" class="color-preview"></div>
            </div>
            """
            
        elif widget == 'password':
            return f'<input type="password" {base_attrs}>'
            
        elif widget == 'file':
            return f'<input type="file" {base_attrs}>'
            
        elif widget == 'directory':
            return f'<input type="text" {base_attrs} placeholder="Seleziona directory...">'
            
        elif field_type == 'array':
            return f'<textarea {base_attrs} rows="3" placeholder="Inserisci valori separati da virgola o JSON"></textarea>'
            
        else:  # string di default
            pattern = field.get('pattern', '')
            pattern_attr = f' pattern="{pattern}"' if pattern else ''
            return f'<input type="text" {base_attrs}{pattern_attr}>'
            
    def generate_all_plugin_uis(self) -> List[str]:
        """Genera le UI per tutti i plugin registrati."""
        generated_files = []
        
        for plugin_id in self.config_manager.list_plugins():
            ui_file = self.generate_plugin_ui(plugin_id)
            if ui_file:
                generated_files.append(ui_file)
                
        return generated_files
        
    def generate_plugin_menu(self) -> str:
        """Genera un menu principale per accedere alle configurazioni di tutti i plugin."""
        plugins = []
        
        for plugin_id in self.config_manager.list_plugins():
            ui_metadata = self.config_manager.get_ui_metadata(plugin_id)
            if ui_metadata:
                plugins.append({
                    'id': plugin_id,
                    'name': ui_metadata['plugin_name'],
                    'description': ui_metadata['description'],
                    'version': ui_metadata['version']
                })
                
        menu_html = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configurazione Plugin - LaboonChat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .plugin-card {
            transition: transform 0.2s;
            cursor: pointer;
        }
        .plugin-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .header-gradient {
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
        }
    </style>
</head>
<body>
    <div class="header-gradient py-4">
        <div class="container">
            <h1><i class="bi bi-gear-fill"></i> Configurazione Plugin</h1>
            <p class="mb-0">Gestisci le impostazioni dei tuoi plugin LaboonChat</p>
        </div>
    </div>
    
    <div class="container my-4">
        <div class="row">"""
        
        for plugin in plugins:
            card_html = f"""
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card plugin-card h-100" onclick="openPluginConfig('{plugin['id']}')">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="bi bi-puzzle"></i> {plugin['name']}
                        </h5>
                        <p class="card-text">{plugin['description']}</p>
                        <small class="text-muted">Versione: {plugin['version']}</small>
                    </div>
                    <div class="card-footer">
                        <small class="text-muted">
                            <i class="bi bi-gear"></i> Clicca per configurare
                        </small>
                    </div>
                </div>
            </div>
            """
            menu_html += card_html
            
        menu_html += """
        </div>
    </div>
    
    <script>
        function openPluginConfig(pluginId) {
            window.open(`${pluginId}_config.html`, '_blank');
        }
    </script>
</body>
</html>"""
        
        # Salva menu
        menu_file = self.output_dir / "plugin_menu.html"
        with open(menu_file, 'w', encoding='utf-8') as f:
            f.write(menu_html)
            
        logger.info(f"Menu plugin generato: {menu_file}")
        return str(menu_file)