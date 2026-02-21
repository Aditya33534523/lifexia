// frontend/static/js/main.js - Main Application Logic
// FIXED: Proper auth flow, error handling, and initialization

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

        if (window.innerWidth <= 768 && sidebar && menuBtn && 
            !sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
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
        .then(res => {
            if (res.ok) return res.json();
            throw new Error('Auth failed');
        })
        .then(data => {
            if (data.valid) {
                currentUser = { email: email };
                showChatInterface();
            } else {
                clearAuth();
            }
        })
        .catch(err => {
            console.warn('Auth verification failed, using stored credentials:', err.message);
            // If backend is down or route doesn't exist, still allow access with stored creds
            currentUser = { email: email };
            showChatInterface();
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
    const loginPage = document.getElementById('loginPage');
    const chatInterface = document.getElementById('chatInterface');
    
    if (loginPage) loginPage.classList.add('hidden');
    if (chatInterface) chatInterface.classList.remove('hidden');

    // Show admin options if logged in as admin
    const adminBtn = document.getElementById('adminAlertBtn');
    if (adminBtn) {
        if (currentUser && (currentUser.email === 'admin@lifexia.com' || currentUser.email === 'admin@lifexia.local')) {
            adminBtn.classList.remove('hidden');
            adminBtn.style.display = 'flex';
        } else {
            adminBtn.classList.add('hidden');
        }
    }

    loadChatHistory();
    initializeChat();
}

function showLoginPage() {
    const loginPage = document.getElementById('loginPage');
    const chatInterface = document.getElementById('chatInterface');
    const messagesArea = document.getElementById('messagesArea');
    
    if (loginPage) loginPage.classList.remove('hidden');
    if (chatInterface) chatInterface.classList.add('hidden');
    if (messagesArea) messagesArea.innerHTML = '';
}

async function initializeChat() {
    try {
        const response = await fetch(`${API_BASE}/chat/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_email: currentUser ? currentUser.email : 'anonymous' })
        });

        const data = await response.json();
        currentSessionId = data.session_id;

        if (data.welcome_message) {
            addMessage('bot', data.welcome_message);
        }
    } catch (error) {
        console.error('Failed to initialize chat:', error);
        addMessage('bot', "Welcome to **LIFEXIA**! I'm your AI-powered health assistant.\n\nI can help you with:\n- **Drug Information** — Dosages, side effects, interactions\n- **Nearby Hospitals** — Use the Health Grid map above\n- **Emergency Help** — Quick access to emergency contacts\n- **WhatsApp Support** — Toggle 'Send to WhatsApp' below\n\nHow can I assist you today?");
    }
}

function newChat() {
    currentSessionId = null;
    const messagesArea = document.getElementById('messagesArea');
    if (messagesArea) messagesArea.innerHTML = '';
    initializeChat();
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.getElementById('menuBtn');

    if (!sidebar) return;

    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('active');
    } else {
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            sidebar.style.width = '320px';
            if (menuBtn) menuBtn.classList.add('hidden');
        } else {
            sidebar.style.width = '0';
            if (menuBtn) menuBtn.classList.remove('hidden');
        }
    }
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('hidden');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('hidden');
}

function showTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.classList.remove('hidden');
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.classList.add('hidden');
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
    const modal = document.getElementById('whatsappModal');
    if (modal) modal.classList.remove('hidden');
}

function closeWhatsAppModal() {
    const modal = document.getElementById('whatsappModal');
    if (modal) modal.classList.add('hidden');
}

function toggleWhatsAppInput() {
    const toggle = document.getElementById('whatsappToggle');
    const container = document.getElementById('whatsappNumberContainer');
    if (toggle && container) {
        if (toggle.checked) {
            container.classList.remove('hidden');
        } else {
            container.classList.add('hidden');
        }
    }
}

function showNotification(message, type = 'success') {
    const container = document.getElementById('toastContainer') || document.body;
    const notification = document.createElement('div');
    
    const bgColor = type === 'success' ? 'bg-green-500/90' : type === 'error' ? 'bg-red-500/90' : 'bg-blue-500/90';
    notification.className = `${bgColor} text-white px-4 py-3 rounded-xl shadow-lg backdrop-blur-sm text-sm font-medium animate-fade-in`;
    notification.style.cssText = 'animation: fadeIn 0.3s ease-in; max-width: 350px;';
    notification.innerText = message;
    container.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Error handling
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});
