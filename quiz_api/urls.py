from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'quizzes', views.QuizViewSet, basename='quiz')
router.register(r'sessions', views.GameSessionViewSet, basename='gamesession')
router.register(r'players', views.PlayerViewSet, basename='player')

urlpatterns = [
    # Include all router URLs (this creates /api/quizzes/, /api/sessions/, etc.)
    path('', include(router.urls)),

    # Additional custom endpoints
    path('my-quizzes/', views.user_quizzes, name='user_quizzes'),
    path('sessions/<int:pk>/current_question/', views.get_current_question, name='session-current-question'),

    # Test AI service endpoint
    path('test-ai/', views.test_ai_service, name='test_ai_service'),
]