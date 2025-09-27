/**
 * P2P Messaging Web Interface
 * ===========================
 * 🌐 Decentralized connections across digital networks 🌊
 * 
 * Main JavaScript for the P2P messaging web interface.
 * Handles WebSocket connections, real-time messaging, and UI interactions.
 */

class P2PMessaging {
    constructor() {
        this.ws = null;
        this.token = window.P2P_TOKEN;
        this.wsUrl = window.P2P_WS_URL;
        this.contacts = {};
        this.messages = {};
        this.activeContact = null;
        this.isConnected = false;
        
        this.init();
    }
    
    async init() {
        console.log('🌐 Initializing P2P Messaging...');
        
        // Remove loading screen
        this.hideLoading();
        
        // Create main UI
        this.createMainUI();
        
        // Load initial data
        await this.loadContacts();
        
        // Setup WebSocket
        this.connectWebSocket();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('🌐 P2P Messaging initialized successfully!');
    }
    
    hideLoading() {
        const loading = document.querySelector('.loading');
        if (loading) {
            loading.style.opacity = '0';
            setTimeout(() => loading.remove(), 300);
        }
    }
    
    createMainUI() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="app-container">
                <div class="sidebar">
                    <div class="sidebar-header">
                        <h1>🌐 P2P Messaging</h1>
                        <p class="tagline">Decentralized connections with individual responsibility</p>
                    </div>
                    <div class="contacts-list" id="contacts-list">
                        <div class="loading-contacts">Loading contacts...</div>
                    </div>
                </div>
                
                <div class="chat-area">
                    <div class="chat-header" id="chat-header">
                        <div class="no-contact-selected">
                            <div class="whale">🐋</div>
                            <p>Select a contact to start chatting</p>
                        </div>
                    </div>
                    
                    <div class="messages-container" id="messages-container">
                        <div class="no-messages">
                            <p>Select a contact to view messages</p>
                        </div>
                    </div>
                    
                    <div class="message-input-container" id="message-input-container" style="display: none;">
                        <form class="message-input-form" id="message-form">
                            <textarea 
                                class="message-input" 
                                id="message-input" 
                                placeholder="Type a message..."
                                rows="1"
                            ></textarea>
                            <button type="submit" class="send-button" id="send-button">
                                📤
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        `;
    }
    
    async loadContacts() {
        try {
            const response = await fetch('/api/contacts');
            const data = await response.json();
            
            this.contacts = {};
            data.contacts.forEach(contact => {
                this.contacts[contact.id] = contact;
            });
            
            this.renderContacts();
        } catch (error) {
            console.error('Failed to load contacts:', error);
            this.showError('Failed to load contacts');
        }
    }
    
    renderContacts() {
        const contactsList = document.getElementById('contacts-list');
        
        if (Object.keys(this.contacts).length === 0) {
            contactsList.innerHTML = '<div class="no-contacts">No contacts yet</div>';
            return;
        }
        
        const contactsHtml = Object.values(this.contacts).map(contact => {
            const securityIcon = contact.key_type === 'solid' ? '🔒' : '💧';
            const securityClass = contact.key_type === 'solid' ? 'solid-key' : 'liquid-key';
            const securityColor = contact.key_type === 'solid' ? '#d4af37' : '#4a9eff';
            
            const statusEmoji = {
                'online': '🟢',
                'away': '🟡',
                'offline': '⚫'
            }[contact.status] || '⚫';
            
            const trustColor = this.getTrustColor(contact.trust_level);
            
            return `
                <div class="contact-card ${securityClass}" data-contact-id="${contact.id}">
                    <div class="contact-avatar">
                        ${contact.avatar}
                        <div class="status-indicator">${statusEmoji}</div>
                    </div>
                    <div class="contact-info">
                        <div class="contact-name">${contact.name}</div>
                        <div class="contact-meta">
                            <span class="security-indicator" style="color: ${securityColor}">
                                ${securityIcon}
                            </span>
                            <span class="last-seen">${contact.last_seen}</span>
                        </div>
                        <div class="trust-bar">
                            <div class="trust-fill" style="width: ${contact.trust_level}%; background: ${trustColor}"></div>
                            <span class="trust-level">${contact.trust_level}%</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        contactsList.innerHTML = contactsHtml;
    }
    
    getTrustColor(trustLevel) {
        if (trustLevel >= 90) return '#4ade80';
        if (trustLevel >= 70) return '#d4af37';
        if (trustLevel >= 50) return '#f59e0b';
        return '#ef4444';
    }
    
    async selectContact(contactId) {
        if (this.activeContact === contactId) return;
        
        // Update active contact
        this.activeContact = contactId;
        
        // Update UI
        this.updateActiveContactUI();
        this.renderChatHeader();
        
        // Load messages
        await this.loadMessages(contactId);
        
        // Show message input
        document.getElementById('message-input-container').style.display = 'block';
    }
    
    updateActiveContactUI() {
        // Remove active class from all contacts
        document.querySelectorAll('.contact-card').forEach(card => {
            card.classList.remove('active');
        });
        
        // Add active class to selected contact
        if (this.activeContact) {
            const activeCard = document.querySelector(`[data-contact-id="${this.activeContact}"]`);
            if (activeCard) {
                activeCard.classList.add('active');
            }
        }
    }
    
    renderChatHeader() {
        const chatHeader = document.getElementById('chat-header');
        
        if (!this.activeContact || !this.contacts[this.activeContact]) {
            chatHeader.innerHTML = `
                <div class="no-contact-selected">
                    <div class="whale">🐋</div>
                    <p>Select a contact to start chatting</p>
                </div>
            `;
            return;
        }
        
        const contact = this.contacts[this.activeContact];
        
        const securityBadge = contact.key_type === 'solid' ? `
            <div class="security-badge solid">
                <span class="security-icon">🔒</span>
                <span class="security-text">Solid Key</span>
                <div class="security-pulse"></div>
            </div>
        ` : `
            <div class="security-badge liquid">
                <span class="security-icon">💧</span>
                <span class="security-text">Liquid Key</span>
                <div class="security-wave"></div>
            </div>
        `;
        
        chatHeader.innerHTML = `
            <div class="contact-info">
                <div class="contact-avatar">${contact.avatar}</div>
                <div class="contact-details">
                    <h3>${contact.name}</h3>
                    <p class="contact-status">${contact.status}</p>
                </div>
            </div>
            ${securityBadge}
            <div class="trust-indicator">
                <div class="trust-circle" style="--trust-level: ${contact.trust_level}%">
                    <span>${contact.trust_level}%</span>
                </div>
            </div>
        `;
    }
    
    async loadMessages(contactId) {
        try {
            const response = await fetch(`/api/messages/${contactId}`);
            const data = await response.json();
            
            this.messages[contactId] = data.messages || [];
            this.renderMessages();
        } catch (error) {
            console.error('Failed to load messages:', error);
            this.showError('Failed to load messages');
        }
    }
    
    renderMessages() {
        const messagesContainer = document.getElementById('messages-container');
        
        if (!this.activeContact || !this.messages[this.activeContact]) {
            messagesContainer.innerHTML = '<div class="no-messages">Start a conversation!</div>';
            return;
        }
        
        const messages = this.messages[this.activeContact];
        
        if (messages.length === 0) {
            messagesContainer.innerHTML = '<div class="no-messages">Start a conversation!</div>';
            return;
        }
        
        const messagesHtml = messages.map(message => {
            const senderClass = message.sender === 'me' ? 'sent' : 'received';
            const encryptionIcon = message.encrypted !== false ? '🔐' : '⚠️';
            const verificationIcon = message.verified !== false ? '✅' : '❌';
            
            // Format timestamp
            let timeStr = 'now';
            try {
                const dt = new Date(message.timestamp);
                timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } catch (e) {
                // Use default
            }
            
            return `
                <div class="message ${senderClass}">
                    <div class="message-content">
                        <p>${this.escapeHtml(message.text)}</p>
                        <div class="message-meta">
                            <span class="message-time">${timeStr}</span>
                            <span class="security-indicators">
                                <span title="Encrypted">${encryptionIcon}</span>
                                <span title="Verified">${verificationIcon}</span>
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        messagesContainer.innerHTML = messagesHtml;
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async sendMessage(text) {
        if (!this.activeContact || !text.trim()) return;
        
        try {
            const response = await fetch('/api/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contact_id: this.activeContact,
                    text: text.trim()
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'sent') {
                // Message will be added via WebSocket
                console.log('Message sent successfully');
            } else {
                throw new Error('Failed to send message');
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            this.showError('Failed to send message');
        }
    }
    
    connectWebSocket() {
        if (this.ws) {
            this.ws.close();
        }
        
        console.log('🔌 Connecting to WebSocket...');
        this.ws = new WebSocket(this.wsUrl);
        
        this.ws.onopen = () => {
            console.log('🔌 WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        this.ws.onclose = () => {
            console.log('🔌 WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            // Reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('🔌 WebSocket error:', error);
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_message':
                this.handleNewMessage(data.message);
                break;
            case 'typing':
                this.handleTypingIndicator(data);
                break;
            case 'pong':
                // Handle ping/pong
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }
    
    handleNewMessage(message) {
        // Add message to local storage
        if (!this.messages[message.contact_id]) {
            this.messages[message.contact_id] = [];
        }
        this.messages[message.contact_id].push(message);
        
        // Update UI if this is the active contact
        if (this.activeContact === message.contact_id) {
            this.renderMessages();
        }
        
        // Show notification if not active contact
        if (this.activeContact !== message.contact_id && message.sender !== 'me') {
            this.showNotification(message);
        }
    }
    
    handleTypingIndicator(data) {
        // TODO: Implement typing indicators
        console.log('Typing indicator:', data);
    }
    
    showNotification(message) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const contact = this.contacts[message.contact_id];
            const contactName = contact ? contact.name : 'Unknown';
            
            new Notification(`${contactName} - P2P Messaging`, {
                body: message.text,
                icon: '/static/icon.png'
            });
        }
    }
    
    updateConnectionStatus(connected) {
        // TODO: Add connection status indicator to UI
        console.log('Connection status:', connected ? 'Connected' : 'Disconnected');
    }
    
    setupEventListeners() {
        // Contact selection
        document.addEventListener('click', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                const contactId = contactCard.dataset.contactId;
                this.selectContact(contactId);
            }
        });
        
        // Message form
        const messageForm = document.getElementById('message-form');
        messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('message-input');
            const text = input.value.trim();
            
            if (text) {
                this.sendMessage(text);
                input.value = '';
                this.autoResizeTextarea(input);
            }
        });
        
        // Auto-resize textarea
        const messageInput = document.getElementById('message-input');
        messageInput.addEventListener('input', (e) => {
            this.autoResizeTextarea(e.target);
        });
        
        // Enter to send (Shift+Enter for new line)
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                messageForm.dispatchEvent(new Event('submit'));
            }
        });
        
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showError(message) {
        // TODO: Implement proper error notifications
        console.error('Error:', message);
        alert(message); // Temporary
    }
}

// Initialize P2P Messaging when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.p2pMessaging = new P2PMessaging();
});

// Handle page visibility for connection management
document.addEventListener('visibilitychange', () => {
    if (window.p2pMessaging) {
        if (document.hidden) {
            // Page is hidden, can reduce activity
        } else {
            // Page is visible, ensure connection is active
            if (!window.p2pMessaging.isConnected) {
                window.p2pMessaging.connectWebSocket();
            }
        }
    }
});