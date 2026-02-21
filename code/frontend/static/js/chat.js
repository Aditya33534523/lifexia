// frontend/static/js/chat.js - Chat Functionality
// FIXED: Correct API endpoint (/chat/message instead of /chat/query)
// FIXED: Proper error handling and response parsing

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addMessage('user', message);
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    // WhatsApp Integration
    const whatsappToggle = document.getElementById('whatsappToggle');
    const sendWhatsApp = whatsappToggle ? whatsappToggle.checked : false;
    const whatsappNumberEl = document.getElementById('whatsappNumber');
    const whatsappNumber = whatsappNumberEl ? whatsappNumberEl.value.trim() : '';

    if (sendWhatsApp && !whatsappNumber) {
        hideTypingIndicator();
        showNotification('Please enter a WhatsApp number', 'error');
        return;
    }

    try {
        // Use /chat/message endpoint (matches chat_routes.py)
        const response = await fetch(`${API_BASE}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            },
            body: JSON.stringify({
                message: message,
                user_email: currentUser ? currentUser.email : 'anonymous',
                session_id: currentSessionId,
                send_whatsapp: sendWhatsApp,
                whatsapp_number: whatsappNumber
            })
        });

        const data = await response.json();

        hideTypingIndicator();

        if (response.ok && data.response) {
            addMessage('bot', data.response);

            // Update session ID if returned
            if (data.session_id && !currentSessionId) {
                currentSessionId = data.session_id;
            }

            // Show WhatsApp notification if applicable
            if (data.whatsapp) {
                if (data.whatsapp.sent) {
                    showNotification('✅ Message also sent to WhatsApp!', 'success');
                } else {
                    showNotification('❌ WhatsApp send failed: ' + (data.whatsapp.error || 'Unknown error'), 'error');
                }
            }

            // Reload chat history sidebar
            loadChatHistory();
        } else {
            const errorMsg = data.error || data.response || 'Sorry, I encountered an error. Please try again.';
            addMessage('bot', errorMsg);
        }
    } catch (error) {
        console.error('Send message error:', error);
        hideTypingIndicator();
        addMessage('bot', 'Connection error. Please check your internet connection and try again.');
    }
}

function addMessage(type, content, timestamp = null) {
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;

    const time = timestamp || formatTime();

    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${type === 'user' ? 'justify-end' : 'justify-start'} message-enter`;

    let formattedContent = '';
    if (type === 'user') {
        formattedContent = `<p class="text-white whitespace-pre-wrap">${escapeHtml(content)}</p>`;
    } else {
        // Use marked for bot messages (Markdown support)
        try {
            let parser = null;
            if (typeof marked !== 'undefined') {
                if (typeof marked.parse === 'function') {
                    parser = marked.parse;
                } else if (typeof marked === 'function') {
                    parser = marked;
                }
            }

            if (parser) {
                formattedContent = `<div class="text-white markdown-content">${parser(content)}</div>`;
            } else {
                // Fallback: basic markdown formatting
                const basicFormatted = content
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/## (.*?)$/gm, '<h3 class="text-lg font-bold mt-3 mb-1">$1</h3>')
                    .replace(/### (.*?)$/gm, '<h4 class="font-bold mt-2 mb-1">$1</h4>')
                    .replace(/^- (.*?)$/gm, '<li class="ml-4">$1</li>')
                    .replace(/\n/g, '<br>');
                formattedContent = `<div class="text-white markdown-content">${basicFormatted}</div>`;
            }
        } catch (e) {
            console.error('Markdown parsing failed:', e);
            formattedContent = `<p class="text-white whitespace-pre-wrap">${escapeHtml(content)}</p>`;
        }
    }

    messageDiv.innerHTML = `
        <div class="max-w-[85%] sm:max-w-[70%] ${type === 'user' ? 'glassmorphism-strong' : 'glassmorphism'} rounded-2xl p-4 shadow-lg">
            ${formattedContent}
            <span class="text-white/50 text-xs mt-2 block">${time}</span>
        </div>
    `;

    messagesArea.appendChild(messageDiv);

    // Smooth scroll to bottom
    messagesArea.scrollTo({
        top: messagesArea.scrollHeight,
        behavior: 'smooth'
    });
}

async function loadChatHistory() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_BASE}/history/${currentUser.email}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            }
        });

        if (!response.ok) return;

        const history = await response.json();
        const historyList = document.getElementById('chatHistoryList');

        if (!historyList) return;

        if (!Array.isArray(history) || history.length === 0) {
            historyList.innerHTML = `
                <div class="text-white/50 text-sm text-center py-4">
                    No chat history yet
                </div>
            `;
            return;
        }

        historyList.innerHTML = history.map(chat => `
            <div class="glassmorphism-strong rounded-xl p-3 hover:bg-white/30 transition-all cursor-pointer group" onclick="loadConversation('${chat.session_id}')">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-white text-sm font-medium truncate">${escapeHtml(chat.title || 'Untitled Chat')}</h3>
                        <p class="text-white/60 text-xs mt-1 truncate">${chat.last_message || 'No messages'}</p>
                    </div>
                    <button onclick="deleteConversation(event, ${chat.id})" class="opacity-0 group-hover:opacity-100 transition-opacity ml-2 text-white/60 hover:text-red-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
                <div class="flex items-center text-white/40 text-xs mt-2">
                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    ${new Date(chat.created_at).toLocaleDateString()}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

async function loadConversation(sessionId) {
    try {
        showLoading();

        const response = await fetch(`${API_BASE}/history/conversation/${sessionId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            }
        });

        const data = await response.json();

        // Clear current messages
        const messagesArea = document.getElementById('messagesArea');
        if (messagesArea) messagesArea.innerHTML = '';
        currentSessionId = sessionId;

        // Load all messages
        if (data.messages && Array.isArray(data.messages)) {
            data.messages.forEach(msg => {
                addMessage(
                    msg.role === 'user' ? 'user' : 'bot',
                    msg.content,
                    msg.timestamp ? formatTime(new Date(msg.timestamp)) : null
                );
            });
        }

        hideLoading();

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) sidebar.classList.remove('active');
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
        hideLoading();
        showNotification('Failed to load conversation', 'error');
    }
}

async function deleteConversation(event, conversationId) {
    event.stopPropagation();

    if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/history/delete/${conversationId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            }
        });

        if (response.ok) {
            showNotification('Conversation deleted', 'success');
            loadChatHistory();
        } else {
            showNotification('Failed to delete conversation', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Failed to delete conversation', 'error');
    }
}
