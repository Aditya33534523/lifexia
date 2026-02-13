// frontend/static/js/main.js - Main Application Logic
const API_BASE = '/api';
let currentUser = null;
let currentSessionId = null;
let sidebarOpen = true;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('LifeXia initializing...');
    setupEventListeners();
    checkAuthStatus();
});

function setupEventListeners() {
    // Enter key for message input
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Enter key for login
    const loginPassword = document.getElementById('loginPassword');
    if (loginPassword) {
        loginPassword.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleLogin();
            }
        });
    }

    // Click outside sidebar to close (mobile)
    document.addEventListener('click', (e) => {
        const sidebar = document.getElementById('sidebar');
        const menuBtn = document.getElementById('menuBtn');

        if (window.innerWidth <= 768 && sidebar && !sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    });
}

function checkAuthStatus() {
    const token = localStorage.getItem('lifexia_token');
    const email = localStorage.getItem('lifexia_email');

    if (token && email) {
        // Verify token with backend
        fetch(`${API_BASE}/auth/verify`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        })
            .then(res => res.json())
            .then(data => {
                if (data.valid) {
                    currentUser = { email: email };
                    showChatInterface();
                } else {
                    clearAuth();
                }
            })
            .catch(err => {
                console.error('Auth verification failed:', err);
                clearAuth();
            });
    }
}

function clearAuth() {
    localStorage.removeItem('lifexia_token');
    localStorage.removeItem('lifexia_email');
    currentUser = null;
    currentSessionId = null;
}

function showChatInterface() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('chatInterface').classList.remove('hidden');

    // Show admin options if logged in as admin
    const adminBtn = document.getElementById('adminAlertBtn');
    if (adminBtn) {
        if (currentUser && (currentUser.email === 'admin@lifexia.com' || currentUser.email === 'admin@lifexia.local')) {
            adminBtn.classList.remove('hidden');
        } else {
            adminBtn.classList.add('hidden');
        }
    }

    loadChatHistory();
    initializeChat();
}

function showLoginPage() {
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('chatInterface').classList.add('hidden');
    document.getElementById('messagesArea').innerHTML = '';
}

async function initializeChat() {
    try {
        const response = await fetch(`${API_BASE}/chat/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_email: currentUser.email })
        });

        const data = await response.json();
        currentSessionId = data.session_id;

        if (data.welcome_message) {
            addMessage('bot', data.welcome_message);
        }
    } catch (error) {
        console.error('Failed to initialize chat:', error);
        addMessage('bot', 'Welcome to LifeXia! I\'m here to help you with medication information, drug interactions, dosage guidelines, and more. How can I assist you today?');
    }
}

function newChat() {
    currentSessionId = null;
    document.getElementById('messagesArea').innerHTML = '';
    initializeChat();
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.getElementById('menuBtn');

    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('active');
    } else {
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            sidebar.style.width = '320px';
            menuBtn.classList.add('hidden');
        } else {
            sidebar.style.width = '0';
            menuBtn.classList.remove('hidden');
        }
    }
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showTypingIndicator() {
    document.getElementById('typingIndicator').classList.remove('hidden');
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(date = new Date()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}


function showWhatsAppModal() {
    document.getElementById('whatsappModal').classList.remove('hidden');
}

function closeWhatsAppModal() {
    document.getElementById('whatsappModal').classList.add('hidden');
}



function toggleWhatsAppInput() {
    const toggle = document.getElementById('whatsappToggle');
    const container = document.getElementById('whatsappNumberContainer');
    if (toggle.checked) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `toast-notification toast-${type}`;
    notification.innerText = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Error handling
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});
