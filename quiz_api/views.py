from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
import logging

from .models import Quiz, Question, GameSession, Player, PlayerAnswer
from .serializers import (
    QuizSerializer, QuizCreateSerializer, GameSessionSerializer,
    PlayerSerializer, JoinQuizSerializer, SubmitAnswerSerializer,
    QuestionSerializer, PlayerAnswerSerializer
)
from .ai_service import QuizAIService

logger = logging.getLogger(__name__)


class QuizViewSet(viewsets.ModelViewSet):
    """ViewSet for Quiz CRUD operations and AI generation"""
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter quizzes based on user"""
        queryset = super().get_queryset()
        if self.action == 'list':
            # Only show user's own quizzes in list view
            return queryset.filter(host=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Set the host to the current user"""
        serializer.save(host=self.request.user)

    @action(detail=False, methods=['post'], serializer_class=QuizCreateSerializer)
    def create_with_ai(self, request):
        """Create a quiz with AI-generated questions"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract data
        title = serializer.validated_data['title']
        topic = serializer.validated_data['topic']
        difficulty = serializer.validated_data.get('difficulty', 'medium')

        try:
            with transaction.atomic():
                # Create the quiz
                quiz = Quiz.objects.create(
                    host=request.user,
                    title=title,
                    topic=topic,
                    difficulty=difficulty
                )

                # Generate questions with AI
                ai_service = QuizAIService()
                try:
                    questions_data = ai_service.generate_quiz_questions(
                        topic=topic,
                        difficulty=difficulty,
                        num_questions=10
                    )
                except Exception as e:
                    logger.warning(f"AI service failed, using sample questions: {str(e)}")
                    # Fallback to sample questions
                    questions_data = ai_service.generate_sample_questions(topic, difficulty)

                # Create question objects
                for idx, q_data in enumerate(questions_data):
                    Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        correct_answer=q_data['correct_answer'],
                        wrong_answers=q_data['wrong_answers'],
                        order=idx
                    )

                # Update user stats
                request.user.total_quizzes_hosted += 1
                request.user.save()

                # Return the created quiz with questions
                quiz_serializer = QuizSerializer(quiz)
                return Response(quiz_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating quiz: {str(e)}")
            return Response(
                {'error': 'Failed to create quiz. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Start a new game session for a quiz"""
        quiz = self.get_object()

        # Check if quiz has questions
        if not quiz.questions.exists():
            return Response(
                {'error': 'Quiz has no questions'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new session
        session = GameSession.objects.create(quiz=quiz)

        serializer = GameSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a quiz"""
        quiz = self.get_object()
        quiz.is_active = False
        quiz.save()

        return Response({'status': 'Quiz deactivated'})


class GameSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for game session management"""
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer
    permission_classes = [AllowAny]  # Allow anyone to join games

    @action(detail=False, methods=['post'], serializer_class=JoinQuizSerializer)
    def join(self, request):
        """Join a quiz session with a join code"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        join_code = serializer.validated_data['join_code']
        nickname = serializer.validated_data['nickname']

        # Find active quiz with this code
        quiz = get_object_or_404(
            Quiz,
            join_code=join_code.upper(),
            is_active=True
        )

        # Get or create active session
        session = GameSession.objects.filter(
            quiz=quiz,
            status__in=['waiting', 'active']
        ).first()

        if not session:
            session = GameSession.objects.create(quiz=quiz)

        # Check if nickname already exists in session
        if session.players.filter(nickname=nickname).exists():
            return Response(
                {'error': 'Nickname already taken in this session'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create player
        player = Player.objects.create(
            session=session,
            nickname=nickname
        )

        # Return player and session info
        return Response({
            'player': PlayerSerializer(player).data,
            'session': GameSessionSerializer(session).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def start_game(self, request, pk=None):
        """Start the game (host only)"""
        session = self.get_object()

        # Check if user is the host
        if request.user != session.quiz.host:
            return Response(
                {'error': 'Only the host can start the game'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if there are players
        if not session.players.exists():
            return Response(
                {'error': 'No players have joined yet'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Start the game
        session.status = 'active'
        session.started_at = timezone.now()
        session.save()

        # Get first question
        first_question = session.quiz.questions.first()

        return Response({
            'status': 'Game started',
            'current_question': QuestionSerializer(first_question).data
        })

    @action(detail=True, methods=['post'])
    def next_question(self, request, pk=None):
        """Move to the next question (host only)"""
        session = self.get_object()

        # Check if user is the host
        if request.user != session.quiz.host:
            return Response(
                {'error': 'Only the host can control questions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Increment question index
        session.current_question_index += 1

        # Check if quiz is complete
        total_questions = session.quiz.questions.count()
        if session.current_question_index >= total_questions:
            session.status = 'finished'
            session.ended_at = timezone.now()
            session.save()

            # Return final results
            return Response({
                'status': 'Quiz completed',
                'final_scores': PlayerSerializer(
                    session.players.filter(is_active=True),
                    many=True
                ).data
            })

        session.save()

        # Get current question
        current_question = session.quiz.questions.all()[session.current_question_index]

        return Response({
            'current_question': QuestionSerializer(current_question).data,
            'question_number': session.current_question_index + 1,
            'total_questions': total_questions
        })

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """Get current leaderboard"""
        session = self.get_object()
        players = session.players.filter(is_active=True).order_by('-score', 'joined_at')

        return Response({
            'leaderboard': PlayerSerializer(players, many=True).data,
            'session_status': session.status
        })


class PlayerViewSet(viewsets.ModelViewSet):
    """ViewSet for player actions"""
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'], serializer_class=SubmitAnswerSerializer)
    def submit_answer(self, request, pk=None):
        """Submit an answer for the current question"""
        player = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_id = serializer.validated_data['question_id']
        selected_answer = serializer.validated_data['selected_answer']
        time_taken = serializer.validated_data['time_taken']

        # Get the question
        question = get_object_or_404(Question, id=question_id)

        # Check if question belongs to the session's quiz
        if question.quiz != player.session.quiz:
            return Response(
                {'error': 'Invalid question for this quiz'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if player already answered this question
        if PlayerAnswer.objects.filter(player=player, question=question).exists():
            return Response(
                {'error': 'Already answered this question'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if answer is correct
        is_correct = selected_answer == question.correct_answer

        # Calculate score (base 100 points, bonus for speed)
        score_earned = 0
        if is_correct:
            base_score = 100
            # Bonus points for quick answers (max 50 bonus points)
            time_bonus = max(0, int(50 * (1 - time_taken / question.time_limit)))
            score_earned = base_score + time_bonus

            player.score += score_earned
            player.answers_correct += 1
        else:
            player.answers_wrong += 1

        # Save the answer
        answer = PlayerAnswer.objects.create(
            player=player,
            question=question,
            selected_answer=selected_answer,
            is_correct=is_correct,
            time_taken=time_taken
        )

        player.save()

        return Response({
            'is_correct': is_correct,
            'correct_answer': question.correct_answer,
            'score_earned': score_earned,
            'total_score': player.score
        })

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get player's complete results"""
        player = self.get_object()
        answers = player.answers.select_related('question').order_by('question__order')

        return Response({
            'player': PlayerSerializer(player).data,
            'answers': PlayerAnswerSerializer(answers, many=True).data,
            'quiz_title': player.session.quiz.title
        })