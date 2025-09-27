"""
Template Email per Sistema Protezione Minori Semplificato
Genera email di riepilogo utilizzo per genitori/tutori.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

class MinorProtectionEmailTemplate:
    """Generatore di template email per riepiloghi di utilizzo."""
    
    @staticmethod
    def generate_usage_summary_html(
        user_name: str,
        session_data: Dict[str, Any],
        usage_history: List[Dict[str, Any]],
        period_minutes: int
    ) -> str:
        """Genera email HTML con riepilogo utilizzo."""
        
        # Calcola statistiche
        total_sessions = len(usage_history)
        total_time = sum(session.get('duration_minutes', 0) for session in usage_history)
        total_messages = sum(session.get('messages_sent', 0) for session in usage_history)
        
        # Periodo di riferimento
        now = datetime.now()
        period_start = now - timedelta(minutes=period_minutes)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Riepilogo Utilizzo P2P Messaging - {user_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            color: #666;
            margin: 10px 0 0 0;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        .session-list {{
            margin: 30px 0;
        }}
        .session-item {{
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }}
        .session-time {{
            font-weight: bold;
            color: #007bff;
            font-size: 14px;
        }}
        .session-details {{
            color: #666;
            font-size: 13px;
            margin-top: 5px;
        }}
        .warning-box {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .warning-box h3 {{
            color: #856404;
            margin: 0 0 10px 0;
            font-size: 16px;
        }}
        .warning-box p {{
            color: #856404;
            margin: 5px 0;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 12px;
        }}
        .timestamp {{
            color: #999;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Riepilogo Utilizzo P2P Messaging</h1>
            <p>Utente: <strong>{user_name}</strong></p>
            <p class="timestamp">Periodo: {period_start.strftime('%d/%m/%Y %H:%M')} - {now.strftime('%d/%m/%Y %H:%M')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{total_sessions}</span>
                <div class="stat-label">Sessioni Totali</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{total_time}</span>
                <div class="stat-label">Minuti di Utilizzo</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{total_messages}</span>
                <div class="stat-label">Messaggi Inviati</div>
            </div>
        </div>

        <div class="warning-box">
            <h3>⚠️ Promemoria Importante</h3>
            <p>• Questo è un sistema P2P decentralizzato senza controllo centrale</p>
            <p>• La responsabilità dell'utilizzo sicuro è individuale</p>
            <p>• Verificare sempre con chi si comunica</p>
            <p>• Non condividere mai informazioni personali sensibili</p>
        </div>

        <div class="session-list">
            <h3>📊 Dettaglio Sessioni</h3>
"""

        # Aggiungi dettagli sessioni
        if usage_history:
            for session in usage_history[-10:]:  # Ultime 10 sessioni
                start_time = datetime.fromisoformat(session.get('start_time', ''))
                duration = session.get('duration_minutes', 0)
                messages = session.get('messages_sent', 0)
                
                html_content += f"""
            <div class="session-item">
                <div class="session-time">
                    📅 {start_time.strftime('%d/%m/%Y %H:%M')}
                </div>
                <div class="session-details">
                    ⏱️ Durata: {duration} minuti | 💬 Messaggi: {messages}
                </div>
            </div>
"""
        else:
            html_content += """
            <div class="session-item">
                <div class="session-details">Nessuna sessione registrata in questo periodo</div>
            </div>
"""

        html_content += f"""
        </div>

        <div class="footer">
            <p>📧 Email generata automaticamente dal Sistema di Protezione Minori</p>
            <p>🕒 Generata il {now.strftime('%d/%m/%Y alle %H:%M')}</p>
            <p>⚙️ Frequenza notifiche: ogni {period_minutes} minuti</p>
        </div>
    </div>
</body>
</html>
"""
        return html_content
    
    @staticmethod
    def generate_usage_summary_text(
        user_name: str,
        session_data: Dict[str, Any],
        usage_history: List[Dict[str, Any]],
        period_minutes: int
    ) -> str:
        """Genera email di testo semplice con riepilogo utilizzo."""
        
        # Calcola statistiche
        total_sessions = len(usage_history)
        total_time = sum(session.get('duration_minutes', 0) for session in usage_history)
        total_messages = sum(session.get('messages_sent', 0) for session in usage_history)
        
        # Periodo di riferimento
        now = datetime.now()
        period_start = now - timedelta(minutes=period_minutes)
        
        text_content = f"""
RIEPILOGO UTILIZZO P2P MESSAGING
================================

Utente: {user_name}
Periodo: {period_start.strftime('%d/%m/%Y %H:%M')} - {now.strftime('%d/%m/%Y %H:%M')}

STATISTICHE UTILIZZO
--------------------
• Sessioni Totali: {total_sessions}
• Minuti di Utilizzo: {total_time}
• Messaggi Inviati: {total_messages}

PROMEMORIA IMPORTANTE
---------------------
⚠️  Questo è un sistema P2P decentralizzato senza controllo centrale
⚠️  La responsabilità dell'utilizzo sicuro è individuale
⚠️  Verificare sempre con chi si comunica
⚠️  Non condividere mai informazioni personali sensibili

DETTAGLIO SESSIONI
------------------
"""

        # Aggiungi dettagli sessioni
        if usage_history:
            for session in usage_history[-10:]:  # Ultime 10 sessioni
                start_time = datetime.fromisoformat(session.get('start_time', ''))
                duration = session.get('duration_minutes', 0)
                messages = session.get('messages_sent', 0)
                
                text_content += f"""
📅 {start_time.strftime('%d/%m/%Y %H:%M')}
   Durata: {duration} minuti | Messaggi: {messages}
"""
        else:
            text_content += "\nNessuna sessione registrata in questo periodo\n"

        text_content += f"""

---
📧 Email generata automaticamente dal Sistema di Protezione Minori
🕒 Generata il {now.strftime('%d/%m/%Y alle %H:%M')}
⚙️ Frequenza notifiche: ogni {period_minutes} minuti
"""
        return text_content
    
    @staticmethod
    def generate_subject(user_name: str, period_minutes: int) -> str:
        """Genera oggetto email."""
        now = datetime.now()
        return f"🛡️ Riepilogo Utilizzo P2P Messaging - {user_name} ({now.strftime('%d/%m/%Y %H:%M')})"