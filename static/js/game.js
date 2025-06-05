// Game Management
class GameManager {
    constructor() {
        this.sessionId = null;
        this.playerId = null;
        this.currentQuestion = null;
        this.timer = null;
        this.timeLeft = 20;
        this.isHost = false;
        this.initializeGame();
    }

    initializeGame() {
        // Check if we're hosting or playing
        const path = window.location.pathname;
        if (path.includes('/host-game/')) {
            this.initializeHost();
        } else if (path.includes('/play-game/')) {
            this.initializePlayer();
        }
    }

    // HOST FUNCTIONS
    async initializeHost() {
        this.isHost = true;
        const quizId = localStorage.getItem('currentQuizId');
        const joinCode = localStorage.getItem('currentQuizCode');

        if (!quizId || !joinCode) {
            alert('No quiz selected');
            window.location.href = '/dashboard/';
            return;
        }

        // Display join code
        document.getElementById('join-code').textContent = joinCode;

        // Start a new session
        await this.createSession(quizId);

        // Start polling for players
        this.pollForPlayers();
    }

    async createSession(quizId) {
        try {
            const response = await api.startSession(quizId);
            this.sessionId = response.id;
            localStorage.setItem('sessionId', this.sessionId);
        } catch (error) {
            console.error('Error creating session:', error);
        }
    }

    async pollForPlayers() {
        try {
            const response = await api.getSession(this.sessionId);
            const players = response.players || [];

            // Update player count
            document.getElementById('player-count').textContent = players.length;

            // Update player list
            const playerList = document.getElementById('player-list');
            playerList.innerHTML = players.map(player => `
                <div class="player-item">
                    ${player.nickname} - Score: ${player.score}
                </div>
            `).join('');

            // Enable start button if we have players
            const startBtn = document.getElementById('start-btn');
            if (players.length > 0) {
                startBtn.disabled = false;
                startBtn.textContent = `Start Game (${players.length} players)`;
            }

            // Continue polling if game hasn't started
            if (response.status === 'waiting') {
                setTimeout(() => this.pollForPlayers(), 2000);
            }
        } catch (error) {
            console.error('Error polling for players:', error);
        }
    }

    async getCurrentQuestion() {
        try {
            const session = await api.getSession(this.sessionId);
            console.log("sezzion : ", session);
            return session.current_question;
        } catch (error) {
            console.error('Error fetching current question:', error);
            return null;
        }
    }

    async startGame() {
        try {
            const response = await api.startGame(this.sessionId);
            if (response.current_question) {
                document.getElementById('waiting-room').style.display = 'none';
                document.getElementById('game-controls').style.display = 'block';
                this.displayQuestion(response.current_question);
            }
        } catch (error) {
            alert('Error starting game: ' + error.message);
        }
    }

    // PLAYER FUNCTIONS
    async initializePlayer() {
        this.isHost = false;
        const playerData = JSON.parse(localStorage.getItem('playerData') || '{}');

        if (!playerData.player || !playerData.session) {
            alert('No game session found');
            window.location.href = '/join-game/';
            return;
        }

        this.playerId = playerData.player.id;
        this.sessionId = playerData.session.id;

        document.getElementById('player-name').textContent = playerData.player.nickname;
        document.getElementById('score').textContent = playerData.player.score;

        // Start polling for game updates
        this.pollForGameUpdates();
    }

    async pollForGameUpdates() {
        try {
            const response = await api.getSession(this.sessionId);

            if (response.status === 'active') {
                // Game has started
                document.getElementById('waiting').style.display = 'none';
                document.getElementById('question-display').style.display = 'block';
                console.log("response = ", response);
                // Get current question
                const currentQuestion = await this.getCurrentQuestion();
                console.log(currentQuestion);
                if (currentQuestion) {
                    this.displayQuestionForPlayer(currentQuestion);
                }
            } else if (response.status === 'finished') {
                // Game ended
                this.showFinalResults();
            } else {
                // Keep polling
                setTimeout(() => this.pollForGameUpdates(), 1000);
            }
        } catch (error) {
            console.error('Error polling for updates:', error);
        }
    }

    // SHARED FUNCTIONS
    displayQuestion(question) {
        this.currentQuestion = question;

        if (this.isHost) {
            document.getElementById('question-number').textContent = question.order + 1;
            document.getElementById('question-text').textContent = question.question_text;
            console.log(question);
            const answersDiv = document.getElementById('answers');
            const allAnswers = [question.correct_answer, ...question.wrong_answers];
            const shuffled = this.shuffleArray(allAnswers);

            answersDiv.innerHTML = shuffled.map((answer, idx) => `
                <div class="answer-option">${idx + 1}. ${answer}</div>
            `).join('');
        }

        this.startTimer();
    }

    displayQuestionForPlayer(question) {
        this.currentQuestion = question;
        document.getElementById('question-text').textContent = question.question_text;
        console.log("haha -- ", question);
        const allAnswers = [question.correct_answer, ...question.wrong_answers];
        const shuffled = this.shuffleArray(allAnswers);

        const buttons = document.querySelectorAll('.answer-btn');
        shuffled.forEach((answer, idx) => {
            buttons[idx].textContent = answer;
            buttons[idx].dataset.answer = answer;
        });

        this.startTimer();
    }
    

    startTimer() {
        this.timeLeft = 20;
        this.updateTimerDisplay();

        this.timer = setInterval(() => {
            this.timeLeft--;
            this.updateTimerDisplay();

            if (this.timeLeft <= 0) {
                this.stopTimer();
                if (this.isHost) {
                    this.nextQuestion();
                } else {
                    this.showFeedback(false, 0);
                }
            }
        }, 1000);
    }

    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    updateTimerDisplay() {
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = this.timeLeft;
        }
    }

    async selectAnswer(answerIndex) {
        const buttons = document.querySelectorAll('.answer-btn');
        const selectedAnswer = buttons[answerIndex].dataset.answer;
        const timeTaken = 20 - this.timeLeft;

        this.stopTimer();

        try {
            const response = await api.submitAnswer(
                this.playerId,
                this.currentQuestion.id,
                selectedAnswer,
                timeTaken
            );

            this.showFeedback(response.is_correct, response.score_earned);
            document.getElementById('score').textContent = response.total_score;
        } catch (error) {
            console.error('Error submitting answer:', error);
        }
    }

    showFeedback(isCorrect, points) {
        document.getElementById('question-display').style.display = 'none';
        document.getElementById('feedback').style.display = 'block';

        const result = document.getElementById('result');
        result.textContent = isCorrect ? 'Correct! ✓' : 'Wrong! ✗';
        result.style.color = isCorrect ? 'green' : 'red';

        document.getElementById('points').textContent = points;

        // Wait for next question
        setTimeout(() => {
            document.getElementById('feedback').style.display = 'none';
            this.pollForGameUpdates();
        }, 3000);
    }

    async nextQuestion() {
        try {
            const response = await api.nextQuestion(this.sessionId);

            if (response.status === 'Quiz completed') {
                this.showHostResults(response.final_scores);
            } else {
                this.displayQuestion(response.current_question);
            }
        } catch (error) {
            console.error('Error getting next question:', error);
        }
    }

    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    showHostResults(scores) {
        document.getElementById('game-controls').style.display = 'none';
        document.getElementById('leaderboard').innerHTML = `
            <h2>Final Results</h2>
            ${scores.map((player, idx) => `
                <div class="final-score-item">
                    ${idx + 1}. ${player.nickname} - ${player.score} points
                </div>
            `).join('')}
            <button onclick="window.location.href='/dashboard/'">Back to Dashboard</button>
        `;
    }

    async showFinalResults() {
        const response = await api.getPlayerResults(this.playerId);
        document.getElementById('waiting').style.display = 'none';
        document.getElementById('question-display').style.display = 'none';
        document.getElementById('feedback').style.display = 'none';
        document.getElementById('final-results').style.display = 'block';

        document.getElementById('final-score').textContent = response.player.score;
        // Add leaderboard display here
    }
}

// Global functions for HTML
function startGame() {
    gameManager.startGame();
}

function nextQuestion() {
    gameManager.nextQuestion();
}

function selectAnswer(index) {
    gameManager.selectAnswer(index);
}

function showResults() {
    // Show current results
}

// Initialize game manager
const gameManager = new GameManager();

// Add missing API methods
QuizAPI.prototype.startSession = async function(quizId) {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}/start_session/`, {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include'
    });
    return response.json();
};

QuizAPI.prototype.getSession = async function(sessionId) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/`, {
        method: 'GET',
        headers: this.getHeaders()
    });
    return response.json();
};

QuizAPI.prototype.startGame = async function(sessionId) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/start_game/`, {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include'
    });
    return response.json();
};

QuizAPI.prototype.nextQuestion = async function(sessionId) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/next_question/`, {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include'
    });
    return response.json();
};

QuizAPI.prototype.submitAnswer = async function(playerId, questionId, answer, timeTaken) {
    const response = await fetch(`${API_BASE_URL}/players/${playerId}/submit_answer/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
            question_id: questionId,
            selected_answer: answer,
            time_taken: timeTaken
        })
    });
    return response.json();
};

QuizAPI.prototype.getPlayerResults = async function(playerId) {
    const response = await fetch(`${API_BASE_URL}/players/${playerId}/results/`, {
        method: 'GET',
        headers: this.getHeaders()
    });
    return response.json();
};