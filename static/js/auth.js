// Authentication Management
class AuthManager {
  constructor() {
    this.checkAuthStatus();
  }

  checkAuthStatus() {
    // Check if user is logged in
    const username = localStorage.getItem("username");
    const userId = localStorage.getItem("userId");

    console.log("Auth check - Username:", username, "UserID:", userId);

    if (username && userId) {
      this.updateUIForLoggedInUser(username);
      return true;
    }
    return false;
  }

  updateUIForLoggedInUser(username) {
    console.log("Updating UI for logged in user:", username);

    // Update navigation
    const navLinks = document.getElementById("nav-links");
    const userInfo = document.getElementById("user-info");

    if (navLinks) {
      navLinks.style.display = "none";
      console.log("Hidden login/register links");
    }

    if (userInfo) {
      userInfo.style.display = "flex"; // Changed to flex to match CSS
      const usernameSpan = document.getElementById("username");
      if (usernameSpan) {
        usernameSpan.textContent = username;
        console.log("Updated username display to:", username);
      }
    }
  }

  async login(username, password) {
    try {
      console.log("Attempting login for:", username);
      const response = await api.login(username, password);

      console.log("Login response:", response);

      if (response.username && response.id) {
        // Store user data
        localStorage.setItem("username", response.username);
        localStorage.setItem("userId", response.id);

        console.log("Login successful, stored data:", {
          username: response.username,
          id: response.id,
        });

        // Update UI immediately
        this.updateUIForLoggedInUser(response.username);

        // Show success message
        alert("Login successful! Welcome back, " + response.username);

        // Redirect to dashboard instead of home
        window.location.href = "/";
      } else {
        console.error("Login failed:", response);
        alert(
          "Login failed: " + (response.error || "Invalid response from server")
        );
      }
    } catch (error) {
      console.error("Login error:", error);
      alert("Login error: " + error.message);
    }
  }

  async register(username, email, password) {
    try {
      console.log("Attempting registration for:", username);
      const response = await api.register(username, email, password);

      console.log("Registration response:", response);

      if (response.username && response.id) {
        // Store user data
        localStorage.setItem("username", response.username);
        localStorage.setItem("userId", response.id);

        console.log("Registration successful, stored data:", {
          username: response.username,
          id: response.id,
        });

        // Update UI immediately
        this.updateUIForLoggedInUser(response.username);

        // Show success message
        alert("Registration successful! Welcome, " + response.username);

        // Redirect to dashboard
        window.location.href = "/";
      } else {
        console.error("Registration failed:", response);
        alert(
          "Registration failed: " +
            (response.error || "Invalid response from server")
        );
      }
    } catch (error) {
      console.error("Registration error:", error);
      alert("Registration error: " + error.message);
    }
  }

  logout() {
    console.log("Logging out user");

    // Clear all stored data
    localStorage.removeItem("username");
    localStorage.removeItem("userId");
    localStorage.removeItem("authToken");
    localStorage.removeItem("currentQuizId");
    localStorage.removeItem("currentQuizCode");
    localStorage.removeItem("sessionId");
    localStorage.removeItem("playerId");
    localStorage.removeItem("playerData");

    // Make logout API call
    fetch("/api/auth/logout/", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then(() => {
        console.log("Server logout successful");
      })
      .catch((error) => {
        console.error("Server logout error:", error);
      });

    // Show alert and then redirect
    alert("Logged out successfully.");
    window.location.replace("/");
  }

  // Method to check if user is currently logged in
  isLoggedIn() {
    return localStorage.getItem("username") && localStorage.getItem("userId");
  }

  // Method to get current user info
  getCurrentUser() {
    return {
      username: localStorage.getItem("username"),
      userId: localStorage.getItem("userId"),
    };
  }

  clearAuthData() {
    localStorage.removeItem("username");
    localStorage.removeItem("userId");
    localStorage.removeItem("authToken");

    // ADD THESE LINES:
    localStorage.removeItem("playerData");
    localStorage.removeItem("sessionId");
    localStorage.removeItem("playerId");
    localStorage.removeItem("currentQuizId");
    localStorage.removeItem("currentQuizCode");
    localStorage.removeItem("newQuizData");
  }
}

// Helper function to get CSRF token (used in logout)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Initialize auth manager
const auth = new AuthManager();

// Global functions for HTML onclick
function logout() {
  auth.logout();
}

// Global function to check login status (for console debugging)
function checkLoginStatus() {
  const isLoggedIn = auth.isLoggedIn();
  const currentUser = auth.getCurrentUser();

  console.log("=== LOGIN STATUS CHECK ===");
  console.log("Is Logged In:", isLoggedIn);
  console.log("Current User:", currentUser);
  console.log("LocalStorage contents:");
  console.log("- username:", localStorage.getItem("username"));
  console.log("- userId:", localStorage.getItem("userId"));
  console.log("- authToken:", localStorage.getItem("authToken"));
  console.log("========================");

  return { isLoggedIn, currentUser };
}

// Handle login form submission
if (document.getElementById("login-form")) {
  document
    .getElementById("login-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      if (!username || !password) {
        alert("Please enter both username and password");
        return;
      }

      await auth.login(username, password);
    });
}

// Handle registration form submission
if (document.getElementById("register-form")) {
  document
    .getElementById("register-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("username").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;

      if (!username || !email || !password) {
        alert("Please fill in all fields");
        return;
      }

      await auth.register(username, email, password);
    });
}

// Expose functions globally for console debugging
window.checkLoginStatus = checkLoginStatus;
window.auth = auth;
