# MessageHistory Plugin - Ricerca Community Open Source

## Panoramica
Ricerca delle best practices della community open source per l'implementazione di sistemi di message history in applicazioni P2P e chat sicure.

## Fonti Analizzate

### 1. Applicazioni P2P Decentralizzate

#### OrbitDB/Orbit Chat <mcreference link="https://github.com/orbitdb/orbit" index="2">2</mcreference>
- **Architettura**: Chat distribuita serverless su IPFS
- **Storage**: Utilizza OrbitDB come database P2P costruito su IPFS
- **Caratteristiche**:
  - Database decentralizzato per ogni canale chat
  - Sincronizzazione automatica tra peer
  - Nessun single point of failure
  - Supporto per client browser, desktop e terminale

#### IPFS Chat Implementations <mcreference link="https://github.com/lalosh/ipfs-chat" index="3">3</mcreference>
- **Protocollo**: Publish/Subscribe pattern su IPFS
- **Caratteristiche**:
  - Chat globali e private rooms
  - Condivisione file tramite hash IPFS
  - Completamente distribuito tra peer
  - Utilizzo di DHT per peer discovery

#### Textile/IPFS Chat Tutorial <mcreference link="https://medium.com/textileio/build-a-decentralized-chat-app-with-knockout-and-ipfs-fccf11e8ce7b" index="4">4</mcreference>
- **Pattern**: MVVM con IPFS pubsub
- **Tecnologie**: 
  - `ipfs-pubsub-room` per gestione room-based
  - Floodsub per broadcasting messaggi
  - Gossipsub per routing efficiente (futuro)

### 2. Storage e Sincronizzazione

#### IceFireDB-SQLite <mcreference link="https://www.reddit.com/r/ipfs/comments/v9t91g/icefiredbsqlite_interesting_when_p2p_meets_sqlite/" index="1">1</mcreference>
- **Concept**: Integrazione P2P IPFS con SQLite storage engine
- **Vantaggi**: Combina robustezza SQLite con distribuzione IPFS

#### TeaTime Project <mcreference link="https://news.ycombinator.com/item?id=42256104" index="5">5</mcreference>
- **Architettura**: SQLite + IPFS + GitHub per indicizzazione
- **Pattern**:
  - Database locali SQLite per performance
  - IPFS per distribuzione contenuti
  - GitHub per discovery e moderazione
  - Seeding automatico da IndexedDB

### 3. Crittografia e Sicurezza

#### End-to-End Encryption Patterns <mcreference link="https://www.qed42.com/insights/developing-a-real-time-secure-chat-application-like-whatsapp-signal-with-end-to-end-encryption" index="1">1</mcreference>
- **Signal Protocol**: Double Ratchet per forward secrecy
- **Key Management**:
  - Master Key (MK) generata random client-side
  - Key Encryption Key (KEK) derivata da password
  - MK criptata con KEK per storage sicuro

#### Database Encryption Best Practices <mcreference link="https://crypto.stackexchange.com/questions/75217/end-to-end-encrypted-web-chat-app-with-stored-messages-in-database" index="2">2</mcreference>
- **Schema consigliato**:
  - Random IV per ogni messaggio
  - PBKDF2/Argon2 per key derivation
  - Separazione MK/KEK per cambio password
  - Nessuna ricerca server-side (solo client-side)

#### SQLite Encryption <mcreference link="https://azure.github.io/AppService/2016/07/15/Implementing-Client-side-Encryption-with-Azure-Mobile-Apps.html" index="4">4</mcreference> <mcreference link="https://www.sqlite.org/see/doc/trunk/www/readme.wiki" index="5">5</mcreference>
- **SQLite Encryption Extension (SEE)**: Soluzione commerciale
- **SQLCipher**: Alternativa open source
- **Algoritmi supportati**: AES-256 OFB, AES-128 CCM, AES-256 GCM

### 4. Offline Storage Patterns <mcreference link="https://stackoverflow.com/questions/43320171/offline-chat-storage-using-sqlite" index="3">3</mcreference>

#### Schema Database Consigliato
```sql
-- Tabella master per metadati conversazione
CREATE TABLE master_chat (
    message_id TEXT PRIMARY KEY,
    thread_id TEXT,
    from_user TEXT,
    to_user TEXT,
    timestamp INTEGER,
    message_type TEXT
);

-- Tabella dettagli messaggio
CREATE TABLE chat_data (
    message_id TEXT REFERENCES master_chat(message_id),
    message_body TEXT,
    from_email TEXT,
    to_email TEXT,
    file_size INTEGER,
    download_link TEXT,
    encryption_iv TEXT,
    created_at INTEGER
);
```

## Best Practices Identificate

### 1. Architettura Storage
- **Locale**: SQLite per performance e affidabilità offline
- **Distribuito**: IPFS/BitTorrent per sincronizzazione P2P
- **Ibrido**: Combinazione locale + distribuito per resilienza

### 2. Crittografia
- **Client-side only**: Tutto criptato prima del storage
- **Key management**: Schema MK/KEK per flessibilità
- **Forward secrecy**: Rotazione chiavi per sicurezza temporale

### 3. Sincronizzazione
- **Event-driven**: Pubsub pattern per real-time
- **Conflict resolution**: Timestamp-based o vector clocks
- **Offline-first**: Funzionalità completa senza connessione

### 4. Performance
- **Indicizzazione**: Index su timestamp, thread_id, user_id
- **Paginazione**: Caricamento lazy dei messaggi storici
- **Compressione**: Algoritmi efficienti per storage

## Raccomandazioni per LaboonChat

### Architettura Consigliata
1. **Storage locale**: SQLite con schema master_chat + chat_data
2. **Crittografia**: ChaCha20-Poly1305 (già implementato nel core)
3. **Sincronizzazione**: BitTorrent DHT per peer discovery + direct P2P
4. **Offline**: Funzionalità completa senza connessione

### Schema Database
```sql
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    peer_id TEXT,
    created_at INTEGER,
    last_message_at INTEGER,
    message_count INTEGER DEFAULT 0
);

CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id),
    sender_id TEXT,
    recipient_id TEXT,
    content_encrypted BLOB,
    content_iv BLOB,
    timestamp INTEGER,
    message_type TEXT DEFAULT 'text',
    delivery_status TEXT DEFAULT 'pending',
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, timestamp);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
```

### Plugin API Requirements
- `addMessage(conversationId, content, type)`: Aggiunge messaggio
- `getMessages(conversationId, limit, offset)`: Recupera messaggi
- `getConversations(limit, offset)`: Lista conversazioni
- `markAsDelivered(messageId)`: Aggiorna stato delivery
- `searchMessages(query, conversationId?)`: Ricerca full-text
- `exportConversation(conversationId)`: Export per backup
- `importMessages(data)`: Import da backup

### Considerazioni Sicurezza
- Tutti i contenuti criptati con chiavi derivate dall'identità utente
- IV random per ogni messaggio
- Nessun storage di chiavi in chiaro
- Automatic key rotation per forward secrecy
- Secure deletion dei messaggi scaduti

---

*Ricerca completata il: 2025-01-27*
*Fonti: 5 progetti open source analizzati*
*Focus: P2P, sicurezza, performance, offline-first*