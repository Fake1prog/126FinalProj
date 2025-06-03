"""
Test script to verify API functionality
Run this after starting the server: python test_api.py
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'


def test_api():
    # Test user registration
    print("1. Testing user registration...")
    register_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123'
    }

    response = requests.post(f'{BASE_URL}/auth/register/', json=register_data)
    print(f"Registration response: {response.status_code}")
    if response.status_code == 201:
        print("✓ User registered successfully")
    else:
        print(f"✗ Registration failed: {response.json()}")

    # Test login
    print("\n2. Testing login...")
    login_data = {
        'username': 'testuser',
        'password': 'testpassword123'
    }

    session = requests.Session()
    # Inside your test_api() function, for registration:
    response = requests.post(f'{BASE_URL}/auth/register/', json=register_data)
    print(f"Registration response: {response.status_code}")
    if response.status_code == 201:
        print("✓ User registered successfully")
    else:
        print(f"✗ Registration failed: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except requests.exceptions.JSONDecodeError:
            print("Response body is not valid JSON (likely a 404 error page)")
        return

    # Test quiz creation with AI
    print("\n3. Testing quiz creation with AI...")
    quiz_data = {
        'title': 'Ancient Egypt Quiz',
        'topic': 'Ancient Egypt',
        'difficulty': 'medium'
    }

    response = session.post(f'{BASE_URL}/quizzes/create_with_ai/', json=quiz_data)
    print(f"Quiz creation response: {response.status_code}")
    if response.status_code == 201:
        quiz = response.json()
        print(f"✓ Quiz created successfully")
        print(f"  - Title: {quiz['title']}")
        print(f"  - Join Code: {quiz['join_code']}")
        print(f"  - Questions: {len(quiz['questions'])}")
        return quiz['join_code']
    else:
        print(f"✗ Quiz creation failed: {response.json()}")


if __name__ == '__main__':
    print("Testing Quiz Show Platform API...\n")
    test_api()