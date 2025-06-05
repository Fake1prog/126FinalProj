class GameManager {
    constructor() {
        this.sessionId = null;
        this.playerId = null;
        this.currentQuestion = null;
        this.timer = null;
        this.timeLeft = 20;
        this.isHost = false;
        this.pollTimer = null;
        this.questionStartTime = null;
        this.serverTimeOffset = 0; // To sync with server time
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

    // HOST FUNCTIONS - Minimal changes, host just controls flow
    async initializeHost() {
        this.isHost = true;
        const quizId = localStorage.getItem('currentQuizId');
        const joinCode = localStorage.getItem('currentQuizCode');

        if (!quizId || !joinCode) {
            alert('No quiz selected');
            window.location.href = '/dashboard/';
            return;
        }

        document.getElementById('join-code').textContent = joinCode;
        await this.createSession(quizId);
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

            document.getElementById('player-count').textContent = players.length;

            const playerList = document.getElementById('player-list');
            playerList.innerHTML = players.map(player => `
                <div class="player-item">
                    ${player.nickname} - Score: ${player.score}
                </div>
            `).join('');

            const startBtn = document.getElementById('start-btn');
            if (players.length > 0) {
                startBtn.disabled = false;
                startBtn.textContent = `Start Game (${players.length} players)`;
            }

            if (response.status === 'waiting') {
                setTimeout(() => this.pollForPlayers(), 2000);
            }
        } catch (error) {
            console.error('Error polling for players:', error);
        }
    }

    // PLAYER FUNCTIONS - MAJOR UPDATES FOR SYNC
    async initializePlayer() {
        this.isHost = false;

        // Get session ID from URL parameter (from join-game redirect)
        const urlParams = new URLSearchParams(window.location.search);
        const sessionIdFromUrl = urlParams.get('session');

        // Try URL first, then localStorage as fallback
        this.sessionId = sessionIdFromUrl || localStorage.getItem('sessionId');

        const playerData = JSON.parse(localStorage.getItem('playerData') || '{}');

        if (!this.sessionId || !playerData.player) {
            console.error('Missing session or player data');
            alert('No game session found');
            window.location.href = '/join-game/';
            return;
        }

        this.playerId = playerData.player.id;

        console.log(`✅ Player initialized: ${playerData.player.nickname} in session ${this.sessionId}`);

        document.getElementById('player-name').textContent = playerData.player.nickname;
        document.getElementById('score').textContent = playerData.player.score || 0;

        // Calculate server time offset for sync
        await this.syncServerTime();

        // Start FAST polling for game updates - KEY CHANGE!
        this.startFastPolling();
    }

    async syncServerTime() {
        try {
            const requestTime = Date.now();
            const response = await api.getGameState(this.sessionId);
            const responseTime = Date.now();

            if (response.server_time) {
                const serverTime = new Date(response.server_time).getTime();
                const networkDelay = (responseTime - requestTime) / 2;
                this.serverTimeOffset = serverTime - (responseTime - networkDelay);
                console.log(`⏱️ Server time synced, offset: ${this.serverTimeOffset}ms`);
            }
        } catch (error) {
            console.error('Failed to sync server time:', error);
        }
    }

    getServerTime() {
        return Date.now() + this.serverTimeOffset;
    }

    // NEW: Fast polling for real-time updates
    startFastPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
        }

        console.log('🚀 Starting fast polling for game state...');

        // Poll every 500ms during active gameplay for smooth sync
        this.pollTimer = setInterval(async () => {
            try {
                const gameState = await api.getGameState(this.sessionId);
                this.handleGameStateUpdate(gameState);
            } catch (error) {
                console.error('Polling error:', error);
                // If we get repeated errors, slow down polling
                if (this.pollTimer) {
                    clearInterval(this.pollTimer);
                    setTimeout(() => this.startFastPolling(), 2000);
                }
            }
        }, 500); // 500ms = 2 times per second
    }

    // NEW: Handle real-time game state updates
    async handleGameStateUpdate(gameState) {
        console.log('📊 Game state update:', gameState.status, `Q${gameState.current_question_index + 1}`, `${gameState.time_left}s left`);

        if (gameState.status === 'waiting') {
            this.showWaitingState();
            return;
        }

        if (gameState.status === 'finished') {
            this.showFinalResults();
            return;
        }

        if (gameState.status === 'active') {
            // Game is active, check if we need to show new question
            const questionChanged = this.currentQuestion?.id !== gameState.current_question?.id;

            if (questionChanged && gameState.current_question) {
                console.log('📝 New question detected:', gameState.current_question.question_text.substring(0, 50));
                this.currentQuestion = gameState.current_question;
                this.questionStartTime = new Date(gameState.question_start_time);
                this.displayQuestionForPlayer(gameState.current_question);
            }

            // Update timer with server time
            this.updateTimerFromServer(gameState.time_left);

            // Show question interface if not already shown
            if (document.getElementById('waiting').style.display !== 'none') {
                document.getElementById('waiting').style.display = 'none';
                document.getElementById('question-display').style.display = 'block';
            }
        }
    }

    showWaitingState() {
        document.getElementById('waiting').style.display = 'block';
        document.getElementById('question-display').style.display = 'none';
        document.getElementById('feedback').style.display = 'none';
    }

    // UPDATED: Display question without starting local timer
    displayQuestionForPlayer(question) {
        this.currentQuestion = question;
        document.getElementById('question-text').textContent = question.question_text;

        const allAnswers = [question.correct_answer, ...question.wrong_answers];
        const shuffled = this.shuffleArray(allAnswers);

        const buttons = document.querySelectorAll('.answer-btn');
        shuffled.forEach((answer, idx) => {
            if (buttons[idx]) {
                buttons[idx].textContent = answer;
                buttons[idx].dataset.answer = answer;
                buttons[idx].disabled = false; // Re-enable for new question
                buttons[idx].style.opacity = '1';
            }
        });

        // Reset feedback display
        document.getElementById('feedback').style.display = 'none';
        document.getElementById('question-display').style.display = 'block';
    }

    // NEW: Update timer based on server time instead of local timer
    updateTimerFromServer(timeLeft) {
        this.timeLeft = Math.max(0, Math.ceil(timeLeft));
        this.updateTimerDisplay();

        // If time is up, disable answer buttons
        if (this.timeLeft <= 0) {
            this.disableAnswerButtons();
        }
    }

    disableAnswerButtons() {
        const buttons = document.querySelectorAll('.answer-btn');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
        });
    }

    updateTimerDisplay() {
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = this.timeLeft;

            // Add visual warning when time is low
            if (this.timeLeft <= 5) {
                timerElement.style.color = '#dc2626';
                timerElement.style.fontWeight = 'bold';
            } else {
                timerElement.style.color = '#374151';
                timerElement.style.fontWeight = 'normal';
            }
        }
    }

    // UPDATED: Submit answer with server sync
    async selectAnswer(answerIndex) {
        if (this.timeLeft <= 0) {
            console.log('⏰ Time expired, cannot submit answer');
            return;
        }

        const buttons = document.querySelectorAll('.answer-btn');
        if (!buttons[answerIndex]) return;

        const selectedAnswer = buttons[answerIndex].dataset.answer;

        // Calculate time taken based on server time
        let timeTaken = 20;
        if (this.questionStartTime) {
            const now = this.getServerTime();
            const startTime = this.questionStartTime.getTime();
            timeTaken = Math.max(0, (now - startTime) / 1000);
        }

        console.log(`✅ Submitting answer: "${selectedAnswer}" (time: ${timeTaken.toFixed(1)}s)`);

        // Immediately disable all buttons
        this.disableAnswerButtons();

        try {
            const response = await api.submitAnswer(
                this.playerId,
                this.currentQuestion.id,
                selectedAnswer,
                timeTaken
            );

            console.log('📊 Answer result:', response);
            this.showFeedback(response.is_correct, response.score_earned);

            // Update score display
            document.getElementById('score').textContent = response.total_score;

        } catch (error) {
            console.error('Error submitting answer:', error);
            // Re-enable buttons if submission failed
            const buttons = document.querySelectorAll('.answer-btn');
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
        }
    }

    showFeedback(isCorrect, points) {
        document.getElementById('question-display').style.display = 'none';
        document.getElementById('feedback').style.display = 'block';

        const result = document.getElementById('result');
        result.textContent = isCorrect ? 'Correct! ✓' : 'Wrong! ✗';
        result.style.color = isCorrect ? '#16a34a' : '#dc2626';

        document.getElementById('points').textContent = points;

        console.log(`📊 Feedback shown: ${isCorrect ? 'CORRECT' : 'WRONG'} (+${points} points)`);

        // Feedback will be hidden when next question loads via polling
    }

    // SHARED FUNCTIONS (unchanged)
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    async showFinalResults() {
        console.log('🏁 Game finished, showing results');

        if (this.pollTimer) {
            clearInterval(this.pollTimer);
        }

        try {
            const response = await api.getPlayerResults(this.playerId);

            document.getElementById('waiting').style.display = 'none';
            document.getElementById('question-display').style.display = 'none';
            document.getElementById('feedback').style.display = 'none';
            document.getElementById('final-results').style.display = 'block';

            document.getElementById('final-score').textContent = response.player.score;

        } catch (error) {
            console.error('Error loading final results:', error);
        }
    }

    // Cleanup
    cleanup() {
        if (this.timer) {
            clearInterval(this.timer);
        }
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
        }
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

// Initialize game manager
const gameManager = new GameManager();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (gameManager) {
        gameManager.cleanup();
    }
});

// ADD NEW API METHODS
QuizAPI.prototype.getGameState = async function(sessionId) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/game_state/`, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include'
    });

    if (!response.ok) {
        throw new Error(`Failed to get game state: ${response.status}`);
    }

    return response.json();
};

// Updated existing methods to handle timing
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