"""
Interfaccia per la configurazione iniziale dell'identità utente
Include la checkbox per indicare se l'utente è minorenne
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

class IdentitySetupDialog:
    """Dialog per la configurazione iniziale dell'identità utente"""
    
    def __init__(self, parent=None, on_complete: Optional[Callable] = None):
        self.parent = parent
        self.on_complete = on_complete
        self.result = None
        
        # Crea finestra
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Configurazione Identità - LaboonChat")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        
        # Centra la finestra
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Crea i widget dell'interfaccia"""
        
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titolo
        title_label = ttk.Label(main_frame, text="Configurazione Identità", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Nome utente
        ttk.Label(main_frame, text="Nome utente:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Email (opzionale)
        ttk.Label(main_frame, text="Email (opzionale):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(main_frame, textvariable=self.email_var, width=30)
        email_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Separatore
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        # Sezione protezione minori
        protection_frame = ttk.LabelFrame(main_frame, text="Protezione Minori", padding="10")
        protection_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Checkbox minorenne
        self.is_minor_var = tk.BooleanVar()
        minor_checkbox = ttk.Checkbutton(
            protection_frame, 
            text="Sono minorenne", 
            variable=self.is_minor_var,
            command=self._on_minor_status_changed
        )
        minor_checkbox.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Info protezione minori
        info_text = ("Se sei minorenne, il sistema invierà periodicamente "
                    "un riepilogo delle tue attività di chat a un genitore o tutore.")
        info_label = ttk.Label(protection_frame, text=info_text, wraplength=400, 
                              font=('Arial', 9), foreground='gray')
        info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Frame per configurazione genitore (inizialmente nascosto)
        self.parent_frame = ttk.Frame(protection_frame)
        self.parent_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Email genitore
        ttk.Label(self.parent_frame, text="Email genitore/tutore:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.parent_email_var = tk.StringVar()
        parent_email_entry = ttk.Entry(self.parent_frame, textvariable=self.parent_email_var, width=30)
        parent_email_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Intervallo notifiche
        ttk.Label(self.parent_frame, text="Intervallo notifiche (minuti):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.interval_var = tk.StringVar(value="60")
        interval_spinbox = ttk.Spinbox(self.parent_frame, from_=15, to=1440, 
                                      textvariable=self.interval_var, width=10)
        interval_spinbox.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Nascondi inizialmente il frame genitore
        self.parent_frame.grid_remove()
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Annulla", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Conferma", command=self._on_confirm).pack(side=tk.LEFT, padx=5)
        
        # Configura il ridimensionamento
        main_frame.columnconfigure(1, weight=1)
        self.parent_frame.columnconfigure(1, weight=1)
        
    def _on_minor_status_changed(self):
        """Gestisce il cambio di stato della checkbox minorenne"""
        if self.is_minor_var.get():
            self.parent_frame.grid()
            self.window.geometry("500x500")  # Espandi finestra
        else:
            self.parent_frame.grid_remove()
            self.window.geometry("500x400")  # Riduci finestra
            
    def _on_cancel(self):
        """Gestisce l'annullamento"""
        self.result = None
        self.window.destroy()
        
    def _on_confirm(self):
        """Gestisce la conferma"""
        # Validazione
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Errore", "Il nome utente è obbligatorio")
            return
            
        if self.is_minor_var.get():
            parent_email = self.parent_email_var.get().strip()
            if not parent_email:
                messagebox.showerror("Errore", "L'email del genitore è obbligatoria per i minorenni")
                return
            if "@" not in parent_email:
                messagebox.showerror("Errore", "Inserisci un'email valida per il genitore")
                return
        
        # Crea risultato
        self.result = {
            'username': username,
            'email': self.email_var.get().strip(),
            'is_minor': self.is_minor_var.get(),
            'parent_email': self.parent_email_var.get().strip() if self.is_minor_var.get() else "",
            'interval_minutes': int(self.interval_var.get()) if self.is_minor_var.get() else 60
        }
        
        # Configura protezione minori se necessario
        if self.result['is_minor']:
            try:
                protection = SimpleMinorProtection()
                protection.set_minor_status(
                    is_minor=True,
                    parent_email=self.result['parent_email'],
                    user_name=self.result['username']
                )
                protection.start()
                logger.info(f"Minor protection configured for {username}")
            except Exception as e:
                logger.error(f"Failed to configure minor protection: {e}")
                messagebox.showerror("Errore", f"Errore nella configurazione protezione minori: {e}")
                return
        
        # Chiama callback se presente
        if self.on_complete:
            self.on_complete(self.result)
            
        self.window.destroy()
        
    def show(self) -> Optional[Dict]:
        """Mostra il dialog e restituisce il risultato"""
        self.window.wait_window()
        return self.result


def show_identity_setup(parent=None) -> Optional[Dict]:
    """
    Mostra il dialog di configurazione identità
    
    Returns:
        Dict con i dati dell'identità o None se annullato
    """
    dialog = IdentitySetupDialog(parent)
    return dialog.show()


if __name__ == "__main__":
    # Test dell'interfaccia
    result = show_identity_setup()
    if result:
        print("Configurazione completata:", result)
    else:
        print("Configurazione annullata")