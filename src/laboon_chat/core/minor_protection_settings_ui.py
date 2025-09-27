"""
Interfaccia per la gestione delle impostazioni della protezione minori
Include la possibilità di disattivare la protezione quando si diventa maggiorenni
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Optional, Callable
from pathlib import Path

try:
    from .simple_minor_protection import SimpleMinorProtection
except ImportError:
    from simple_minor_protection import SimpleMinorProtection

logger = logging.getLogger(__name__)

class MinorProtectionSettingsDialog:
    """Dialog per la gestione delle impostazioni della protezione minori"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.protection = SimpleMinorProtection()
        
        # Crea finestra
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Impostazioni Protezione Minori - LaboonChat")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        
        # Centra la finestra
        if parent:
            self.window.transient(parent)
            self.window.grab_set()
        
        self._load_current_settings()
        self._create_widgets()
        
    def _load_current_settings(self):
        """Carica le impostazioni correnti"""
        config = self.protection.config
        self.current_is_minor = config.is_minor
        self.current_enabled = config.enabled
        self.current_parent_email = config.parent_email
        self.current_user_name = config.user_name
        self.current_interval = config.interval_minutes
        
    def _create_widgets(self):
        """Crea i widget dell'interfaccia"""
        
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titolo
        title_label = ttk.Label(main_frame, text="Impostazioni Protezione Minori", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Stato corrente
        status_frame = ttk.LabelFrame(main_frame, text="Stato Corrente", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Mostra stato minorenne
        minor_status = "Sì" if self.current_is_minor else "No"
        ttk.Label(status_frame, text=f"Utente minorenne: {minor_status}").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Mostra stato protezione
        protection_status = "Attiva" if self.current_enabled else "Disattiva"
        status_color = "green" if self.current_enabled else "red"
        status_label = ttk.Label(status_frame, text=f"Protezione: {protection_status}")
        status_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        if self.current_parent_email:
            ttk.Label(status_frame, text=f"Email genitore: {self.current_parent_email}").grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Sezione configurazione
        config_frame = ttk.LabelFrame(main_frame, text="Configurazione", padding="10")
        config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Checkbox stato minorenne
        self.is_minor_var = tk.BooleanVar(value=self.current_is_minor)
        minor_checkbox = ttk.Checkbutton(
            config_frame, 
            text="Sono minorenne", 
            variable=self.is_minor_var,
            command=self._on_minor_status_changed
        )
        minor_checkbox.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Checkbox protezione attiva
        self.enabled_var = tk.BooleanVar(value=self.current_enabled)
        enabled_checkbox = ttk.Checkbutton(
            config_frame, 
            text="Protezione attiva", 
            variable=self.enabled_var,
            command=self._on_enabled_changed
        )
        enabled_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Frame per configurazione dettagli
        self.details_frame = ttk.Frame(config_frame)
        self.details_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Nome utente
        ttk.Label(self.details_frame, text="Nome utente:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.user_name_var = tk.StringVar(value=self.current_user_name)
        user_name_entry = ttk.Entry(self.details_frame, textvariable=self.user_name_var, width=30)
        user_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Email genitore
        ttk.Label(self.details_frame, text="Email genitore:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.parent_email_var = tk.StringVar(value=self.current_parent_email)
        parent_email_entry = ttk.Entry(self.details_frame, textvariable=self.parent_email_var, width=30)
        parent_email_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Intervallo notifiche
        ttk.Label(self.details_frame, text="Intervallo notifiche (minuti):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.interval_var = tk.StringVar(value=str(self.current_interval))
        interval_spinbox = ttk.Spinbox(self.details_frame, from_=15, to=1440, 
                                      textvariable=self.interval_var, width=10)
        interval_spinbox.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Sezione disattivazione
        if self.current_is_minor:
            disable_frame = ttk.LabelFrame(main_frame, text="Diventato Maggiorenne?", padding="10")
            disable_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            
            disable_info = ("Se sei diventato maggiorenne, puoi disattivare la protezione minori. "
                           "Verrà inviata una notifica email al genitore.")
            info_label = ttk.Label(disable_frame, text=disable_info, wraplength=500, 
                                  font=('Arial', 9), foreground='gray')
            info_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
            
            ttk.Button(disable_frame, text="Disattiva Protezione (Maggiorenne)", 
                      command=self._disable_for_adult).grid(row=1, column=0, pady=10)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Annulla", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Salva", command=self._on_save).pack(side=tk.LEFT, padx=5)
        
        # Configura il ridimensionamento
        main_frame.columnconfigure(1, weight=1)
        self.details_frame.columnconfigure(1, weight=1)
        
        # Aggiorna visibilità iniziale
        self._update_visibility()
        
    def _on_minor_status_changed(self):
        """Gestisce il cambio di stato minorenne"""
        self._update_visibility()
        
    def _on_enabled_changed(self):
        """Gestisce il cambio di stato protezione"""
        self._update_visibility()
        
    def _update_visibility(self):
        """Aggiorna la visibilità dei controlli"""
        is_minor = self.is_minor_var.get()
        enabled = self.enabled_var.get()
        
        # Se non è minorenne, disabilita automaticamente la protezione
        if not is_minor:
            self.enabled_var.set(False)
            enabled = False
        
        # Mostra/nascondi dettagli in base allo stato
        if enabled and is_minor:
            self.details_frame.grid()
        else:
            self.details_frame.grid_remove()
            
    def _disable_for_adult(self):
        """Disattiva la protezione per utente diventato maggiorenne"""
        result = messagebox.askyesno(
            "Conferma Disattivazione",
            "Sei sicuro di voler disattivare la protezione minori?\n\n"
            "Questa azione:\n"
            "- Disattiverà tutte le notifiche email\n"
            "- Segnerà l'utente come maggiorenne\n"
            "- Invierà una notifica al genitore\n\n"
            "Vuoi continuare?"
        )
        
        if result:
            try:
                # Disattiva la protezione
                self.protection.set_minor_status(False)
                
                messagebox.showinfo(
                    "Protezione Disattivata",
                    "La protezione minori è stata disattivata con successo.\n"
                    "È stata inviata una notifica email al genitore."
                )
                
                self.window.destroy()
                
            except Exception as e:
                logger.error(f"Error disabling protection: {e}")
                messagebox.showerror("Errore", f"Errore nella disattivazione: {e}")
                
    def _on_cancel(self):
        """Gestisce l'annullamento"""
        self.window.destroy()
        
    def _on_save(self):
        """Gestisce il salvataggio"""
        try:
            is_minor = self.is_minor_var.get()
            enabled = self.enabled_var.get()
            
            # Validazione
            if is_minor and enabled:
                parent_email = self.parent_email_var.get().strip()
                if not parent_email:
                    messagebox.showerror("Errore", "L'email del genitore è obbligatoria")
                    return
                if "@" not in parent_email:
                    messagebox.showerror("Errore", "Inserisci un'email valida")
                    return
            
            # Aggiorna configurazione
            if is_minor != self.current_is_minor:
                # Cambio stato minorenne
                if is_minor:
                    self.protection.set_minor_status(
                        is_minor=True,
                        parent_email=self.parent_email_var.get().strip(),
                        user_name=self.user_name_var.get().strip()
                    )
                else:
                    self.protection.set_minor_status(False)
            else:
                # Aggiorna solo configurazione
                self.protection.update_config(
                    enabled=enabled,
                    parent_email=self.parent_email_var.get().strip(),
                    user_name=self.user_name_var.get().strip(),
                    interval_minutes=int(self.interval_var.get())
                )
            
            messagebox.showinfo("Successo", "Impostazioni salvate con successo")
            self.window.destroy()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")


def show_minor_protection_settings(parent=None):
    """
    Mostra il dialog delle impostazioni protezione minori
    """
    dialog = MinorProtectionSettingsDialog(parent)
    dialog.window.wait_window()


if __name__ == "__main__":
    # Test dell'interfaccia
    show_minor_protection_settings()