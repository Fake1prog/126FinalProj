// Quiz Management
class QuizManager {
  constructor() {
    this.currentQuiz = null;
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    const form = document.getElementById("create-quiz-form");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        await this.createQuiz();
      });
    }

    // Load user's quizzes if on dashboard
    if (window.location.pathname.includes("/dashboard/")) {
      this.loadMyQuizzes();
    }
  }

  async createQuiz() {
    const title = document.getElementById("title").value;
    const topic = document.getElementById("topic").value;
    const difficulty = document.getElementById("difficulty").value;

    // Show loading state
    document.getElementById("create-quiz-form").style.display = "none";
    document.getElementById("loading").style.display = "block";

    try {
      const response = await api.createQuizWithAI(title, topic, difficulty);

      if (response.id && response.join_code) {
        // Check for id instead of just join_code
        // Show success state
        document.getElementById("loading").style.display = "none";
        document.getElementById("success").style.display = "block";
        document.getElementById("join-code").textContent = response.join_code;

        // Store quiz data properly
        this.currentQuiz = response;
        localStorage.setItem("currentQuizId", response.id);
        localStorage.setItem("currentQuizCode", response.join_code);
        localStorage.setItem("currentQuizTitle", response.title); // Add this
      } else {
        throw new Error(response.error || "Failed to create quiz");
      }
    } catch (error) {
      document.getElementById("loading").style.display = "none";
      document.getElementById("create-quiz-form").style.display = "block";
      alert("Error creating quiz: " + error.message);
    }
  }

  async loadMyQuizzes() {
    try {
        const response = await api.getMyQuizzes();
        console.log("API Response:", response);
        const container = document.getElementById("my-quizzes");

        const quizzes = response.results || [];

        // Update total quizzes count
        document.getElementById("total-quizzes").textContent = quizzes.length;

        // Count total players across all quizzes (assumes each quiz has a player_count field)
        let totalPlayers = 0;
        for (const quiz of quizzes) {
            totalPlayers += quiz.player_count || 0;
        }

        // Update total players count (guarded)
        const totalPlayersElem = document.getElementById("total-players");
        if (totalPlayersElem) {
            totalPlayersElem.textContent = totalPlayers;
        }

        if (quizzes.length === 0) {
            container.innerHTML = "<p>No quizzes created yet.</p>";
            return;
        }

        container.innerHTML = quizzes
            .map(
                (quiz) => `
                <div class="quiz-card">
                    <h3>${quiz.title}</h3>
                    <p>Topic: ${quiz.topic}</p>
                    <p>Difficulty: ${quiz.difficulty}</p>
                    <p>Join Code: <strong>${quiz.join_code}</strong></p>
                    <p>Created: ${new Date(
                    quiz.created_at
                    ).toLocaleDateString()}</p>
                </div>
            `
            )
            .join("");
    } catch (error) {
        console.error("Error loading quizzes:", error);
        const container = document.getElementById("my-quizzes");
        container.innerHTML =
            "<p>Failed to load quizzes. Please try again later.</p>";
    }
}


  hostQuiz(quizId, joinCode) {
    localStorage.setItem("currentQuizId", quizId);
    localStorage.setItem("currentQuizCode", joinCode);
    window.location.href = "/host-game/";
  }
}

// Global functions for HTML
function startHosting() {
  window.location.href = "/host-game/";
}

function copyCode() {
  const code = document.getElementById("join-code").textContent;
  navigator.clipboard.writeText(code).then(() => {
    alert("Code copied to clipboard!");
  });
}

// Initialize quiz manager
const quizManager = new QuizManager();

// Add to API class (in api.js)
QuizAPI.prototype.getMyQuizzes = async function () {
  const response = await fetch(`${API_BASE_URL}/quizzes/`, {
    method: "GET",
    headers: this.getHeaders(),
    credentials: "include",
  });
  return response.json();
};
