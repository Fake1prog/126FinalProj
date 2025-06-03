from django.db import models
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()


def generate_join_code():
    """Generate a unique 6-character join code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Quiz.objects.filter(join_code=code).exists():
            return code


class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]

    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_quizzes')
    title = models.CharField(max_length=200)
    topic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    join_code = models.CharField(max_length=6, unique=True, default=generate_join_code)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Quizzes'

    def __str__(self):
        return f"{self.title} by {self.host.username}"


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=500)
    wrong_answers = models.JSONField()  # List of 3 wrong answers
    order = models.IntegerField()
    time_limit = models.IntegerField(default=20)  # seconds

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."


class GameSession(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Players'),
        ('active', 'In Progress'),
        ('finished', 'Finished')
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    current_question_index = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session for {self.quiz.title} - {self.status}"


class Player(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=50)
    score = models.IntegerField(default=0)
    answers_correct = models.IntegerField(default=0)
    answers_wrong = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-score', 'joined_at']
        unique_together = ['session', 'nickname']

    def __str__(self):
        return f"{self.nickname} in {self.session}"


class PlayerAnswer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField()
    time_taken = models.FloatField()  # seconds taken to answer
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['player', 'question']

    def __str__(self):
        return f"{self.player.nickname}'s answer to {self.question}"