#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_platform.settings')
django.setup()

from quiz_api.models import Quiz, GameSession, Player
from django.contrib.auth import get_user_model

User = get_user_model()


def debug_sessions():
    print("=== Debugging Sessions and Players ===")

    # 1. List all quizzes
    quizzes = Quiz.objects.all()
    print(f"\nTotal Quizzes: {quizzes.count()}")

    for quiz in quizzes:
        print(f"\nQuiz: {quiz.title}")
        print(f"  ID: {quiz.id}")
        print(f"  Join Code: {quiz.join_code}")
        print(f"  Active: {quiz.is_active}")
        print(f"  Host: {quiz.host.username}")

        # List sessions for this quiz
        sessions = GameSession.objects.filter(quiz=quiz)
        print(f"  Sessions: {sessions.count()}")

        for session in sessions:
            print(f"    Session ID: {session.id}")
            print(f"    Status: {session.status}")
            print(f"    Current Question: {session.current_question_index}")
            print(f"    Created: {session.created_at}")

            # List players in this session
            players = Player.objects.filter(session=session)
            print(f"    Players: {players.count()}")

            for player in players:
                print(f"      - {player.nickname} (Score: {player.score}, Active: {player.is_active})")

    # 2. Test specific session that's failing
    print(f"\n=== Testing Session ID 31 ===")
    try:
        session_31 = GameSession.objects.get(id=31)
        print(f"Session 31 found: {session_31}")
        print(f"  Quiz: {session_31.quiz.title}")
        print(f"  Status: {session_31.status}")

        players = session_31.players.filter(is_active=True).order_by('-score', 'joined_at')
        print(f"  Active Players: {players.count()}")
        for player in players:
            print(f"    - {player.nickname}: {player.score} points")

    except GameSession.DoesNotExist:
        print("Session 31 does not exist!")

        # Find the latest session instead
        latest_session = GameSession.objects.last()
        if latest_session:
            print(f"Latest session is ID: {latest_session.id}")
            print(f"  Quiz: {latest_session.quiz.title}")
            print(f"  Status: {latest_session.status}")
        else:
            print("No sessions found in database!")

    # 3. Check for active quizzes and their sessions
    print(f"\n=== Active Quizzes and Sessions ===")
    active_quizzes = Quiz.objects.filter(is_active=True)

    for quiz in active_quizzes:
        print(f"\nActive Quiz: {quiz.title} (Code: {quiz.join_code})")
        active_sessions = GameSession.objects.filter(
            quiz=quiz,
            status__in=['waiting', 'active']
        )

        print(f"  Active Sessions: {active_sessions.count()}")
        for session in active_sessions:
            print(f"    Session {session.id}: {session.status}")
            print(f"    Players: {session.players.count()}")


if __name__ == "__main__":
    debug_sessions()