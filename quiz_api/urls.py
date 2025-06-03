from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from quiz_api.views import QuizViewSet, GameSessionViewSet, PlayerViewSet

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)
router.register(r'sessions', GameSessionViewSet)
router.register(r'players', PlayerViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('authentication.urls')),
]