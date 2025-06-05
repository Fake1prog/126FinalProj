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
        this.serverTimeOffset = 0;
        this.lastQuestionId = null;
        this.autoAdvanceCount = 0;
        this.initializeGame();
    }

    initializeGame() {
        const path = window.location.pathname;
        if (path.includes('/host-game/')) {
            this.initializeHost();
        } else if (path.includes('/play-game/')) {
            this.initializePlayer();
        }
    }

    // HOST FUNCTIONS (unchanged)
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

    // PLAYER FUNCTIONS - ENHANCED FOR AUTO-ADVANCE
    async initializePlayer() {
        this.isHost = false;

        const urlParams = new URLSearchParams(window.location.search);
        const sessionIdFromUrl = urlParams.get('session');

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

        await this.syncServerTime();
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

    // ENHANCED: Fast polling with auto-advance detection
    startFastPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
        }

        console.log('🚀 Starting fast polling with auto-advance detection...');

        this.pollTimer = setInterval(async () => {
            try {
                const gameState = await api.getGameState(this.sessionId);
                this.handleGameStateUpdate(gameState);
            } catch (error) {
                console.error('Polling error:', error);
                if (this.pollTimer) {
                    clearInterval(this.pollTimer);
                    setTimeout(() => this.startFastPolling(), 2000);
                }
            }
        }, 500); // Poll every 500ms for real-time sync
    }

    // ENHANCED: Handle game state with auto-advance detection
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
            // Check for question changes (manual or auto-advance)
            const questionChanged = this.currentQuestion?.id !== gameState.current_question?.id;

            if (questionChanged && gameState.current_question) {
                const isAutoAdvance = gameState.auto_advanced || false;
                const wasManualAdvance = gameState.manually_advanced || false;

                console.log(`📝 Question change detected: ${this.currentQuestion?.id || 'none'} → ${gameState.current_question.id}`);

                if (isAutoAdvance) {
                    this.autoAdvanceCount++;
                    console.log(`⏰ AUTO-ADVANCE #${this.autoAdvanceCount}: Time expired, moved to question ${gameState.current_question_index + 1}`);
                    this.showAutoAdvanceNotification();
                } else if (wasManualAdvance) {
                    console.log(`👤 MANUAL ADVANCE: Host moved to question ${gameState.current_question_index + 1}`);
                    this.showManualAdvanceNotification();
                } else {
                    console.log(`📝 QUESTION CHANGE: New question ${gameState.current_question_index + 1}`);
                }

                this.currentQuestion = gameState.current_question;
                this.questionStartTime = new Date(gameState.question_start_time);
                this.lastQuestionId = gameState.current_question.id;

                // Clear any feedback and show new question
                this.clearFeedback();
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

    // NEW: Show auto-advance notification
    showAutoAdvanceNotification() {
        this.showTemporaryMessage('⏰ Time expired! Moving to next question...', 'warning', 2000);
    }

    // NEW: Show manual advance notification
    showManualAdvanceNotification() {
        this.showTemporaryMessage('📝 Host advanced to next question', 'info', 2000);
    }

    // NEW: Show temporary message overlay
    showTemporaryMessage(message, type, duration = 3000) {
        // Create overlay if it doesn't exist
        let overlay = document.getElementById('temp-message-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'temp-message-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: ${type === 'warning' ? '#fbbf24' : type === 'info' ? '#3b82f6' : '#16a34a'};
                color: white;
                padding: 20px 30px;
                border-radius: 12px;
                font-size: 1.2rem;
                font-weight: bold;
                z-index: 9999;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                animation: fadeInOut 2s ease-in-out;
                text-align: center;
                min-width: 300px;
            `;
            document.body.appendChild(overlay);
        }

        overlay.textContent = message;
        overlay.style.display = 'block';

        setTimeout(() => {
            if (overlay) {
                overlay.style.display = 'none';
            }
        }, duration);
    }

    // NEW: Clear feedback display
    clearFeedback() {
        document.getElementById('feedback').style.display = 'none';
        document.getElementById('question-display').style.display = 'block';

        // Reset answer buttons state
        const buttons = document.querySelectorAll('.answer-btn');
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.classList.remove('selected', 'correct', 'incorrect');
        });

        // Reset internal state
        this.hasAnswered = false;
        this.selectedAnswer = null;
    }

    showWaitingState() {
        document.getElementById('waiting').style.display = 'block';
        document.getElementById('question-display').style.display = 'none';
        document.getElementById('feedback').style.display = 'none';
    }

    // UPDATED: Display question with enhanced reset
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
                buttons[idx].disabled = false;
                buttons[idx].style.opacity = '1';
                buttons[idx].classList.remove('selected', 'correct', 'incorrect'); // Clear all states
            }
        });

        // Reset feedback display
        document.getElementById('feedback').style.display = 'none';
        document.getElementById('question-display').style.display = 'block';

        // Reset answer state
        this.hasAnswered = false;
        this.selectedAnswer = null;

        console.log(`📝 Question displayed: ${question.question_text.substring(0, 50)}...`);
    }

    // UPDATED: Server-synchronized timer
    updateTimerFromServer(timeLeft) {
        this.timeLeft = Math.max(0, Math.ceil(timeLeft));
        this.updateTimerDisplay();

        // If time is up, disable answer buttons but don't show feedback
        // The auto-advance will handle the transition
        if (this.timeLeft <= 0) {
            this.disableAnswerButtons();
            console.log('⏰ Timer expired, waiting for auto-advance...');
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

            if (this.timeLeft <= 5) {
                timerElement.style.color = '#dc2626';
                timerElement.style.fontWeight = 'bold';
            } else {
                timerElement.style.color = '#374151';
                timerElement.style.fontWeight = 'normal';
            }
        }
    }

    // UPDATED: Submit answer with enhanced feedback
    async selectAnswer(answerIndex) {
        if (this.timeLeft <= 0) {
            console.log('⏰ Time expired, cannot submit answer');
            this.showTemporaryMessage('⏰ Time expired!', 'warning', 1500);
            return;
        }

        if (this.hasAnswered) {
            console.log('✋ Already answered this question');
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

        // Mark as answered and disable buttons immediately
        this.hasAnswered = true;
        this.selectedAnswer = selectedAnswer;
        this.disableAnswerButtons();

        try {
            const response = await api.submitAnswer(
                this.playerId,
                this.currentQuestion.id,
                selectedAnswer,
                timeTaken
            );

            console.log('📊 Answer result:', response);
            this.showFeedback(response.is_correct, response.score_earned, response.correct_answer);

            // Update score display
            document.getElementById('score').textContent = response.total_score;

        } catch (error) {
            console.error('Error submitting answer:', error);
            // Re-enable buttons if submission failed
            this.hasAnswered = false;
            const buttons = document.querySelectorAll('.answer-btn');
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
            this.showTemporaryMessage('❌ Failed to submit answer', 'error', 2000);
        }
    }

    // ENHANCED: Show feedback with correct answer
    showFeedback(isCorrect, points, correctAnswer) {
        // Highlight answers
        const buttons = document.querySelectorAll('.answer-btn');
        buttons.forEach(btn => {
            const answerText = btn.textContent;
            if (answerText === correctAnswer) {
                btn.classList.add('correct');
                btn.style.background = '#dcfce7';
                btn.style.borderColor = '#16a34a';
            } else if (answerText === this.selectedAnswer && !isCorrect) {
                btn.classList.add('incorrect');
                btn.style.background = '#fecaca';
                btn.style.borderColor = '#dc2626';
            }
        });

        // Show feedback after short delay
        setTimeout(() => {
            document.getElementById('question-display').style.display = 'none';
            document.getElementById('feedback').style.display = 'block';

            const result = document.getElementById('result');
            result.textContent = isCorrect ? 'Correct! ✓' : 'Wrong! ✗';
            result.style.color = isCorrect ? '#16a34a' : '#dc2626';

            document.getElementById('points').textContent = points;

            // Show correct answer if wrong
            const correctAnswerEl = document.getElementById('correct-answer');
            if (correctAnswerEl) {
                if (!isCorrect) {
                    correctAnswerEl.style.display = 'block';
                    correctAnswerEl.textContent = `Correct answer: ${correctAnswer}`;
                } else {
                    correctAnswerEl.style.display = 'none';
                }
            }

            console.log(`📊 Feedback shown: ${isCorrect ? 'CORRECT' : 'WRONG'} (+${points} points)`);

            // Feedback will be cleared when next question loads automatically
        }, 1000);
    }

    // SHARED FUNCTIONS
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

            // Show stats about auto-advances
            if (this.autoAdvanceCount > 0) {
                this.showTemporaryMessage(`Game completed! ${this.autoAdvanceCount} questions auto-advanced due to time limits.`, 'info', 5000);
            }

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

        // Clean up temporary message overlay
        const overlay = document.getElementById('temp-message-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    setSyncStatus(message, type) {
        console.log(`📡 Host Status: ${message} (${type})`);

        // Optional: Add a visual status indicator
        const statusElement = document.getElementById('host-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `host-status ${type}`;
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

// ADD UPDATED API METHODS
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