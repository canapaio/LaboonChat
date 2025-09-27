
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
        