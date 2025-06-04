from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from quiz_api.views import QuizViewSet, GameSessionViewSet, PlayerViewSet

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)
router.register(r'sessions', GameSessionViewSet)
router.register(r'players', PlayerViewSet)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/auth/', include('authentication.urls')),

    # Frontend pages - serve HTML templates
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('create-quiz/', TemplateView.as_view(template_name='create-quiz.html'), name='create-quiz'),
    path('quiz-created/', TemplateView.as_view(template_name='quiz-created.html'), name='quiz-created'),
    # Added this line
    path('host-game/', TemplateView.as_view(template_name='host-game.html'), name='host-game'),
    path('join-game/', TemplateView.as_view(template_name='join-game.html'), name='join-game'),
    path('play-game/', TemplateView.as_view(template_name='play-game.html'), name='play-game'),
    path('results/', TemplateView.as_view(template_name='results.html'), name='results'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])