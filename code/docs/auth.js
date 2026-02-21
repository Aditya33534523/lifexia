// frontend/static/js/auth.js - Authentication Logic

async function handleLogin() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
        alert('Please enter both email and password');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('lifexia_token', data.token);
            localStorage.setItem('lifexia_email', email);
            currentUser = { email: email };
            showChatInterface();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred during login. Using demo mode.');
        // For development/demo purposes if backend is not ready
        currentUser = { email: email };
        showChatInterface();
    } finally {
        hideLoading();
    }
}

function handleLogout() {
    clearAuth();
    showLoginPage();
}

function showRegister() {
    alert('Registration is currently handled by the administrator. Please contact support.');
}

function showLogin() {
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('chatInterface').classList.add('hidden');
}
