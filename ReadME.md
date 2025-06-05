# AI THINKS SO!

**AI THINKS SO!** is a web-based, real-time multiplayer quiz platform powered by AI. Users can log in or register, create AI-generated quizzes on any topic and difficulty level, host live quiz sessions, and invite friends to join using a 6-character join code. Participants answer questions in real time, earn points, and see live leaderboards. The platform is built with Django (Python) on the back end and vanilla JavaScript, HTML, and CSS on the front end.

---

## Table of Contents

1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Installation & Setup](#installation--setup)  
4. [Running the Development Server](#running-the-development-server)  
5. [Usage](#usage)  
6. [Deployment](#deployment)  
7. [Web Demo](#web-demo)  
8. [Project Structure](#project-structure)  
9. [Contributing](#contributing)  
10. [License](#license) 

---

## Features

- **User Authentication**  
  - Register a new account  
  - Log in/out securely  
- **AI-Generated Quizzes**  
  - Input quiz title, topic, and difficulty (Easy, Medium, Hard)  
  - Backend API calls an AI service to generate 10 questions automatically  
- **Dashboard (“My Quizzes”)**  
  - View a list of quizzes you have created  
  - See quiz metadata (title, topic, difficulty, join code, number of questions, creation date)  
- **Quiz Creation Flow**  
  1. Fill out “Create New Quiz” form  
  2. Backend calls AI endpoint  
  3. Quiz is persisted in the database with a unique 6-character join code  
- **Hosting a Quiz (Host-​Game)**  
  - Host sees a waiting room with join code and connected players  
  - Start game once at least one player has joined  
  - Advance through questions, track timers, and view real-time responses/standings  
- **Joining a Quiz (Join-​Game)**  
  - Enter a 6-character join code and your nickname  
  - See a live preview of who else has joined  
  - Automatically redirected when the host starts the game  
- **Playing the Quiz (Play-​Game)**  
  - Real-time question display with a countdown timer  
  - Select and submit one of four shuffled answer options  
  - Immediate feedback (correct/incorrect) and points awarded  
  - Live mini-leaderboard updates after each question  
- **Results Screen**  
  - Final leaderboard and individual performance metrics (score, correct/wrong answers)  
- **Responsive Design**  
  - Works across desktop and mobile viewports  
- **CSRF Protection & Session-Based Auth**  
  - Django’s built-in CSRF middleware & session authentication  
- **REST API**  
  - Endpoints for authentication, quiz creation, session management, player actions, etc.  

---

## Tech Stack

- **Back End**  
  - Python 3.x  
  - Django 4.2  
  - Django REST Framework (DRF)  
  - Django CORS Headers  
  - Gunicorn (production WSGI server)  
  - SQLite / PostgreSQL (configurable via Django settings)  
  - Whitenoise (static file serving)  
- **Front End**  
  - HTML5 / CSS3 (custom styles)  
  - Vanilla JavaScript (ES6+)  
  - Fetch API for AJAX calls  
- **Dev & Build Tools**  
  - pipenv / virtualenv (virtual environment)  
  - pip (`requirements.txt`)  
  - git & GitHub  
- **Deployment**  
  - Render (https://one26finalproj-nhp7.onrender.com/)  
  - Gunicorn + WhiteNoise in production  

---

## Prerequisites

- Python 3.8+ installed on your system  
- Git installed  
- (Optional) A PostgreSQL database if you prefer PostgreSQL over SQLite  
- IDE or code editor (e.g., VS Code, PyCharm)  
- (Windows) Git Bash or Windows Command Prompt / PowerShell  
- (macOS/Linux) Terminal  

---

## Installation & Setup

1. **Clone the repository**  
 ```bash
   git clone https://github.com/Fake1prog/126FinalProj.git
   cd 126FinalProj
 ```


2. **Create and activate a virtual environment**  

Windows PowerShell / CMD

```bash
    python -m venv venv
    .\venv\Scripts\activate
 ```

macOS / Linux
```bash
    python3 -m venv venv
    source venv/bin/activate
 ```
 
3. **Install Python dependencies**
```bash
    pip install -r requirements.txt
 ```

4. **Apply database migrations** 
```bash
    python manage.py migrate
 ```

5. **(Optional) Create a superuser** 
```bash
    python manage.py createsuperuser
```
---

## Running the Development Server


## Running the Development Server

With the virtual environment activated and migrations applied, start the Django development server:

```bash
python manage.py runserver
```
By default, the server runs on http://127.0.0.1:8000/.

Open your browser and navigate to:
```bash
http://127.0.0.1:8000/
```

## Usage

1. **Register & Log In**  
   - Visit `/register/` to create a new account.  
   - After registering, you’ll be automatically logged in.  
   - Visit `/login/` to sign in if you already have an account.

2. **Dashboard (My Quizzes)**  
   - After login, you’ll be redirected to the homepage (`/`).  
   - Click **My Quizzes** to view all quizzes you’ve created.

3. **Create a Quiz**  
   - Click **Create New Quiz** on the navbar or dashboard.  
   - Fill in:
     - **Title**: e.g., “AI Fundamentals Quiz”  
     - **Topic**: e.g., “Machine Learning”  
     - **Difficulty**: Easy / Medium / Hard  
   - Submit the form. The AI will generate 10 questions automatically.  
   - After a successful creation, the “Quiz Created!” page displays a **Join Code**.

4. **Hosting a Quiz Session**  
   - From the **Quiz Created!** page, click **Start Hosting**.  
   - **Note:** If the host creates a quiz, they should start the game immediately because the session will expire; otherwise, players will not be able to join.  
   - You’ll enter the host lobby:
     - Displays quiz title and join code.  
     - Shows a live list of joined players (initially empty).  
     - **Start Game** button becomes enabled once at least one player has joined.

5. **Joining a Quiz Session (Player)**  
   - Go to `/join-game/` or click **Join a Quiz** on the homepage.  
   - Enter the 6-character join code (e.g., `ABC123`) and a unique nickname.  
   - After joining:
     - You’ll see a preview of quiz info (title, # of questions).  
     - Once the host starts the game, you’ll be redirected to the play interface.

6. **Playing the Quiz**  
   - **Host View** (after starting):
     - Question text appears with a 20-second timer.  
     - Host sees a grid of players and can manually advance questions (or rely on the timer).  
     - Correct answers are highlighted in green; incorrect in red.  
     - A mini-leaderboard updates after each question.
   - **Player View**:
     - Wait in lobby until the host starts.  
     - When the quiz begins:  
       - Current question appears with shuffled answer options (A–D).  
       - A 20-second timer counts down.  
       - Select one answer and click **Submit Answer**.  
       - Feedback screen shows whether you were correct, points earned, and the correct answer (if incorrect).  
       - Mini-leaderboard displays current standings.  
       - Automatically proceeds to the next question or final results at the end.

7. **Final Results**  
   - After the last question, both host and players see the final leaderboard and scores.  
   - Options to **Play Again** or **Back to Dashboard**.  


## Deployment

This project is deployed on Render. To deploy your own instance:

1. **Create a Render account** (if you don’t have one).  
2. **New Web Service** → Connect your GitHub repo.  
3. **Build Command**:  
```bash
   pip install -r requirements.txt
   python manage.py migrate
```
4. **Start Command**: 
```bash
   gunicorn 126FinalProj.wsgi
``` 
5. **Environment Variables:**: 
    SECRET_KEY (your Django secret key)

    DEBUG (set to False in production)

    Any AI-API credentials used for quiz generation (e.g., OpenAI key)
6. **Publish** → Render will provide a public URL. 

## Web Demo

Check out the live demo:  
[https://one26finalproj-nhp7.onrender.com/](https://one26finalproj-nhp7.onrender.com/)

