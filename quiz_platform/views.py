from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Quiz

def home_view(request):
    return HttpResponse("""
    <html>
        <body>
            <h1>Quiz Show Platform</h1>
            <p>Frontend is being set up...</p>
            <a href="/admin/">Admin Panel</a><br>
            <a href="/api/">API Browser</a>
        </body>
    </html>
    """)

@login_required
def user_quizzes(request):
    quizzes = Quiz.objects.filter(owner=request.user)
    data = [
        {
            'id': quiz.id,
            'title': quiz.title,
            'created_at': quiz.created_at.strftime('%Y-%m-%d'),
        }
        for quiz in quizzes
    ]
    return JsonResponse({'quizzes': data})

