from . import views
from django.urls import path, include



urlpatterns=[
    path('api/my-quizzes/', views.user_quizzes, name='user_quizzes'), 
    path('sessions/<int:pk>/current_question/', views.get_current_question, name='session-current-question'),
]