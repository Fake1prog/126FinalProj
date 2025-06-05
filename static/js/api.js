    // API Configuration
    const API_BASE_URL = '/api';

    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // API Helper Class
    class QuizAPI {
        constructor() {
            this.token = localStorage.getItem('authToken');
        }

        // Set authorization header
        getHeaders() {
            const headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            };
            if (this.token) {
                headers['Authorization'] = `Token ${this.token}`;
            }
            return headers;
        }

        // Auth endpoints
        async register(username, email, password) {
            const response = await fetch(`${API_BASE_URL}/auth/register/`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include',
                body: JSON.stringify({ username, email, password })
            });
            return response.json();
        }

        async login(username, password) {
            const response = await fetch(`${API_BASE_URL}/auth/login/`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include',
                body: JSON.stringify({ username, password })
            });
            return response.json();
        }

        // Quiz endpoints
        async createQuizWithAI(title, topic, difficulty) {
            console.log('Creating quiz with credentials...');

            const response = await fetch(`${API_BASE_URL}/quizzes/create_with_ai/`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include',  // CRITICAL: This must be here!
                body: JSON.stringify({ title, topic, difficulty })
            });

            console.log('Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return response.json();
        }

        async getMyQuizzes() {
            const response = await fetch(`${API_BASE_URL}/quizzes/`, {
                method: 'GET',
                headers: this.getHeaders(),
                credentials: 'include'
            });
            return response.json();
        }

        async startSession(quizId) {
            const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}/start_session/`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include'
            });
            return response.json();
        }

        // Session endpoints
        async joinQuiz(joinCode, nickname) {
            const response = await fetch(`${API_BASE_URL}/sessions/join/`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    join_code: joinCode,
                    nickname: nickname
                })
            });
            return response.json();
        }

        async getSession(sessionId) {
            const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/`, {
                method: 'GET',
                headers: this.getHeaders(),
                credentials: 'include'
            });
            return response.json();
        }

        async startGame(sessionId) {
            const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/start_game/`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include'
            });
            return response.json();
        }

        async nextQuestion(sessionId) {
            const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/next_question/`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include'
            });
            return response.json();
        }

        // Player endpoints
        async submitAnswer(playerId, questionId, answer, timeTaken) {
            const response = await fetch(`${API_BASE_URL}/players/${playerId}/submit_answer/`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include',
                body: JSON.stringify({
                    question_id: questionId,
                    selected_answer: answer,
                    time_taken: timeTaken
                })
            });
            return response.json();
        }

        async getPlayerResults(playerId) {
            const response = await fetch(`${API_BASE_URL}/players/${playerId}/results/`, {
                method: 'GET',
                headers: this.getHeaders(),
                credentials: 'include'
            });
            return response.json();
        }

        async getCurrentQuestion(sessionId) {
            const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/current_question/`, {
                method: 'GET',
                headers: this.getHeaders(),
                credentials: 'include'
            });
        
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`Failed to fetch current question (status: ${response.status})`);
            }
        
            return response.json();
        }
    }

    // Create global API instance
    const api = new QuizAPI();