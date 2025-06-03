from django.contrib import admin
from .models import Quiz, Question, GameSession, Player, PlayerAnswer


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'host', 'join_code', 'is_active', 'created_at']
    list_filter = ['difficulty', 'is_active', 'created_at']
    search_fields = ['title', 'topic', 'join_code']
    readonly_fields = ['join_code', 'created_at', 'updated_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'question_text_preview']
    list_filter = ['quiz']
    ordering = ['quiz', 'order']

    def question_text_preview(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'status', 'current_question_index', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'session', 'score', 'is_active', 'joined_at']
    list_filter = ['is_active', 'joined_at']
    search_fields = ['nickname']


@admin.register(PlayerAnswer)
class PlayerAnswerAdmin(admin.ModelAdmin):
    list_display = ['player', 'question', 'is_correct', 'time_taken', 'answered_at']
    list_filter = ['is_correct', 'answered_at']