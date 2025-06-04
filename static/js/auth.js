// Authentication Management
class AuthManager {
    constructor() {
        this.checkAuthStatus();
    }

    checkAuthStatus() {
        // Check if user is logged in
        const username = localStorage.getItem('username');
        if (username) {
            this.updateUIForLoggedInUser(username);
        }
    }

    updateUIForLoggedInUser(username) {
        // Update navigation
        const navLinks = document.getElementById('nav-links');
        const userInfo = document.getElementById('user-info');

        if (navLinks) navLinks.style.display = 'none';
        if (userInfo) {
            userInfo.style.display = 'block';
            const usernameSpan = document.getElementById('username');
            if (usernameSpan) usernameSpan.textContent = username;
        }
    }

    async login(username, password) {
        try {
            const response = await api.login(username, password);
            if (response.username) {
                localStorage.setItem('username', response.username);
                localStorage.setItem('userId', response.id);
                window.location.href = '/';
            } else {
                alert('Login failed: ' + (response.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Login error: ' + error.message);
        }
    }

    async register(username, email, password) {
        try {
            const response = await api.register(username, email, password);
            if (response.username) {
                localStorage.setItem('username', response.username);
                localStorage.setItem('userId', response.id);
                window.location.href = '/';
            } else {
                alert('Registration failed: ' + (response.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Registration error: ' + error.message);
        }
    }

    logout() {
        localStorage.removeItem('username');
        localStorage.removeItem('userId');
        localStorage.removeItem('authToken');
        window.location.href = '/';
    }
}

// Initialize auth manager
const auth = new AuthManager();

// Global functions for HTML onclick
function logout() {
    auth.logout();
}

// Handle login form submission
if (document.getElementById('login-form')) {
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        await auth.login(username, password);
    });
}

// Handle registration form submission
if (document.getElementById('register-form')) {
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        await auth.register(username, email, password);
    });
}