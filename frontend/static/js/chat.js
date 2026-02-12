// frontend/static/js/chat.js - Chat Functionality

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addMessage('user', message);
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            },
            body: JSON.stringify({
                message: message,
                user_email: currentUser.email,
                session_id: currentSessionId
            })
        });

        const data = await response.json();

        hideTypingIndicator();

        if (response.ok) {
            addMessage('bot', data.response);
            if (!currentSessionId) {
                currentSessionId = data.session_id;
            }
            // Reload chat history to show new conversation
            loadChatHistory();
        } else {
            addMessage('bot', 'Sorry, I encountered an error. Please try again.');
        }
    } catch (error) {
        console.error('Send message error:', error);
        hideTypingIndicator();
        addMessage('bot', 'Connection error. Please check your internet connection and try again.');
    }
}

function addMessage(type, content, timestamp = null) {
    const messagesArea = document.getElementById('messagesArea');
    const time = timestamp || formatTime();

    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${type === 'user' ? 'justify-end' : 'justify-start'} message-enter`;

    let formattedContent = '';
    if (type === 'user') {
        formattedContent = `<p class="text-white whitespace-pre-wrap">${escapeHtml(content)}</p>`;
    } else {
        // Use marked for bot messages (Markdown support)
        try {
            // Some versions of marked use marked.parse, others just marked()
            const parser = typeof marked.parse === 'function' ? marked.parse : (typeof marked === 'function' ? marked : null);
            if (parser) {
                formattedContent = `<div class="text-white markdown-content">${parser(content)}</div>`;
            } else {
                console.warn('Marked parser not found, falling back to raw text');
                formattedContent = `<p class="text-white whitespace-pre-wrap">${escapeHtml(content)}</p>`;
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
    try {
        const response = await fetch(`${API_BASE}/history/${currentUser.email}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            }
        });

        if (!response.ok) return;

        const history = await response.json();
        const historyList = document.getElementById('chatHistoryList');

        if (history.length === 0) {
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
        document.getElementById('messagesArea').innerHTML = '';
        currentSessionId = sessionId;

        // Load all messages
        data.messages.forEach(msg => {
            addMessage(
                msg.role === 'user' ? 'user' : 'bot',
                msg.content,
                formatTime(new Date(msg.timestamp))
            );
        });

        hideLoading();

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.remove('active');
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
