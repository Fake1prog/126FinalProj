from rest_framework import serializers
from .models import Quiz, Question, GameSession, Player, PlayerAnswer
from authentication.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'total_quizzes_hosted', 'total_quizzes_played']
        read_only_fields = ['total_quizzes_hosted', 'total_quizzes_played']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'correct_answer', 'wrong_answers', 'order', 'time_limit']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    host_username = serializers.CharField(source='host.username', read_only=True)
    question_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'topic', 'difficulty', 'join_code',
            'is_active', 'created_at', 'host_username',
            'questions', 'question_count'
        ]
        read_only_fields = ['join_code', 'created_at', 'questions']


class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['title', 'topic', 'difficulty']


class PlayerSerializer(serializers.ModelSerializer):
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 'nickname', 'score', 'answers_correct',
            'answers_wrong', 'joined_at', 'is_active', 'rank'
        ]

    def get_rank(self, obj):
        # Get rank within the session
        players = obj.session.players.filter(is_active=True).order_by('-score', 'joined_at')
        for idx, player in enumerate(players, 1):
            if player.id == obj.id:
                return idx
        return None


class GameSessionSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    players = PlayerSerializer(many=True, read_only=True)
    total_questions = serializers.IntegerField(source='quiz.questions.count', read_only=True)
    current_question = serializers.SerializerMethodField() 
    
    class Meta:
        model = GameSession
        fields = [
            'id', 'quiz', 'quiz_title', 'status', 'current_question_index',
            'started_at', 'ended_at', 'created_at', 'players', 'total_questions', 'current_question'
        ]
        read_only_fields = ['created_at', 'started_at', 'ended_at']
    
    def get_current_question(self, obj):
        # Get ordered questions from quiz
        questions = obj.quiz.questions.all().order_by('order')
        index = obj.current_question_index or 0
        if 0 <= index < questions.count():
            question = questions[index]
            return QuestionSerializer(question).data
        return None


class PlayerAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = PlayerAnswer
        fields = [
            'id', 'question', 'question_text', 'selected_answer',
            'is_correct', 'time_taken', 'answered_at'
        ]


class JoinQuizSerializer(serializers.Serializer):
    join_code = serializers.CharField(max_length=6)
    nickname = serializers.CharField(max_length=50)


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_answer = serializers.CharField(max_length=500)
    time_taken = serializers.FloatField()