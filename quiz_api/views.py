from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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

        # Always filter by current user for all actions
        user_quizzes = queryset.filter(host=self.request.user).order_by('-created_at')

        logger.info(f"User {self.request.user.username} requesting quizzes")
        logger.info(f"Found {user_quizzes.count()} quizzes for user")

        return user_quizzes

    def list(self, request, *args, **kwargs):
        """Override list to add detailed logging"""
        logger.info(f"LIST request from user: {request.user}")
        logger.info(f"User authenticated: {request.user.is_authenticated}")

        if not request.user.is_authenticated:
            logger.error("User not authenticated for quiz list")
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        queryset = self.get_queryset()
        logger.info(f"Queryset count: {queryset.count()}")

        # Debug: List all quizzes for this user
        for quiz in queryset:
            logger.info(f"Quiz: {quiz.id} - {quiz.title} - Host: {quiz.host.username}")

        serializer = self.get_serializer(queryset, many=True)

        response_data = {
            'results': serializer.data,
            'count': len(serializer.data),
            'user': request.user.username
        }

        logger.info(f"Returning {len(serializer.data)} quizzes")
        return Response(response_data)

    def perform_create(self, serializer):
        """Set the host to the current user"""
        logger.info(f"Creating quiz for user: {self.request.user}")
        quiz = serializer.save(host=self.request.user)
        logger.info(f"Quiz created with ID: {quiz.id}, Host: {quiz.host.username}")

    @action(detail=False, methods=['post'], serializer_class=QuizCreateSerializer)
    def create_with_ai(self, request):
        """Create a quiz with AI-generated questions"""
        logger.info(f"AI Quiz creation request from user: {request.user}")

        if not request.user.is_authenticated:
            logger.error("User not authenticated for AI quiz creation")
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract data
        title = serializer.validated_data['title']
        topic = serializer.validated_data['topic']
        difficulty = serializer.validated_data.get('difficulty', 'medium')

        logger.info(f"Creating AI quiz: {title} about {topic} ({difficulty})")

        try:
            with transaction.atomic():
                # Create the quiz
                quiz = Quiz.objects.create(
                    host=request.user,
                    title=title,
                    topic=topic,
                    difficulty=difficulty
                )

                logger.info(f"Quiz created: ID={quiz.id}, Host={quiz.host.username}")

                # Generate questions with AI
                ai_service = QuizAIService()
                try:
                    questions_data = ai_service.generate_quiz_questions(
                        topic=topic,
                        difficulty=difficulty,
                        num_questions=5
                    )
                    logger.info(f"AI generated {len(questions_data)} questions")
                except Exception as e:
                    logger.warning(f"AI service failed, using sample questions: {str(e)}")
                    # Fallback to sample questions
                    questions_data = ai_service.generate_sample_questions(topic, difficulty)

                # Create question objects
                for idx, q_data in enumerate(questions_data):
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        correct_answer=q_data['correct_answer'],
                        wrong_answers=q_data['wrong_answers'],
                        order=idx
                    )
                    logger.info(f"Created question {idx + 1}: {question.question_text[:50]}...")

                # Update user stats (if field exists)
                try:
                    request.user.total_quizzes_hosted = getattr(request.user, 'total_quizzes_hosted', 0) + 1
                    request.user.save()
                    logger.info(f"Updated user stats: {request.user.total_quizzes_hosted} total quizzes")
                except Exception as e:
                    logger.warning(f"Could not update user stats: {e}")

                # Return the created quiz with questions
                quiz_serializer = QuizSerializer(quiz)
                logger.info(f"Quiz creation successful: {quiz.title} (ID: {quiz.id})")
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

        logger.info(f"Starting session for quiz: {quiz.id} by user: {request.user}")

        # Check if quiz has questions
        if not quiz.questions.exists():
            logger.error(f"Quiz {quiz.id} has no questions")
            return Response(
                {'error': 'Quiz has no questions'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new session
        session = GameSession.objects.create(quiz=quiz)
        logger.info(f"Session created: {session.id} for quiz: {quiz.id}")

        serializer = GameSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a quiz"""
        quiz = self.get_object()
        quiz.is_active = False
        quiz.save()

        logger.info(f"Quiz {quiz.id} deactivated by user: {request.user}")
        return Response({'status': 'Quiz deactivated'})


class GameSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for game session management"""
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer
    permission_classes = [AllowAny]  # Allow anyone to join games

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post'], serializer_class=JoinQuizSerializer)
    def join(self, request):
        """Join a quiz session with a join code"""
        print(f"JOIN REQUEST: {request.data}")  # Debug log

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(f"SERIALIZER ERRORS: {serializer.errors}")  # Debug log
            return Response(
                {'error': f'Invalid data: {serializer.errors}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        join_code = serializer.validated_data['join_code']
        nickname = serializer.validated_data['nickname']

        print(f"LOOKING FOR QUIZ: join_code={join_code}, nickname={nickname}")  # Debug log

        # Find active quiz with this code
        try:
            quiz = Quiz.objects.get(
                join_code=join_code.upper(),
                is_active=True
            )
            print(f"FOUND QUIZ: {quiz.title} (ID: {quiz.id})")  # Debug log
        except Quiz.DoesNotExist:
            print(f"QUIZ NOT FOUND: {join_code}")  # Debug log
            return Response(
                {'error': f'Quiz with code {join_code} not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create active session
        session = GameSession.objects.filter(
            quiz=quiz,
            status__in=['waiting', 'active']
        ).first()

        if not session:
            session = GameSession.objects.create(quiz=quiz)
            print(f"CREATED NEW SESSION: {session.id}")  # Debug log
        else:
            print(f"USING EXISTING SESSION: {session.id}")  # Debug log

        # Check if nickname already exists in session
        if session.players.filter(nickname=nickname).exists():
            print(f"NICKNAME ALREADY EXISTS: {nickname}")  # Debug log
            return Response(
                {'error': f'Nickname "{nickname}" already taken in this session'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create player
        try:
            player = Player.objects.create(
                session=session,
                nickname=nickname
            )
            print(f"CREATED PLAYER: {player.nickname} (ID: {player.id})")  # Debug log
        except Exception as e:
            print(f"ERROR CREATING PLAYER: {str(e)}")  # Debug log
            return Response(
                {'error': f'Failed to create player: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return player and session info
        response_data = {
            'player': PlayerSerializer(player).data,
            'session': GameSessionSerializer(session).data
        }
        print(f"JOIN SUCCESS: {response_data}")  # Debug log

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def game_state(self, request, pk=None):
        """Get current game state with precise timing and response tracking"""
        try:
            session = self.get_object()

            # Get current question with timing
            questions = session.quiz.questions.all().order_by('order')
            total_questions = questions.count()
            current_question = None
            time_left = 0
            question_start_time = None
            auto_advanced = False
            responses_received = 0

            if session.status == 'active' and session.current_question_index < total_questions:
                current_question = questions[session.current_question_index]

                # Calculate time left based on when question started
                if session.question_started_at:
                    question_start_time = session.question_started_at
                else:
                    # Fallback to session updated time
                    question_start_time = session.updated_at or timezone.now()

                elapsed = (timezone.now() - question_start_time).total_seconds()
                time_left = max(0, 20 - elapsed)  # 20 second questions

                # FIXED: Count responses for current question
                responses_received = PlayerAnswer.objects.filter(
                    player__session=session,
                    question=current_question,
                    player__is_active=True
                ).count()

                # 🚀 AUTO-ADVANCE LOGIC: If time is up, automatically move to next question
                if time_left <= 0:
                    logger.info(
                        f"⏰ Auto-advancing from question {session.current_question_index + 1} due to time expiry")

                    # Move to next question
                    session.current_question_index += 1

                    # Check if quiz is complete
                    if session.current_question_index >= total_questions:
                        session.status = 'finished'
                        session.ended_at = timezone.now()
                        session.save()

                        # Return final results
                        players = session.players.filter(is_active=True).order_by('-score', 'joined_at')
                        return Response({
                            'session_id': session.id,
                            'status': 'finished',
                            'current_question_index': session.current_question_index,
                            'total_questions': total_questions,
                            'final_scores': PlayerSerializer(players, many=True).data,
                            'players': PlayerSerializer(players, many=True).data,  # Add this for compatibility
                            'player_count': players.count(),  # Add this
                            'server_time': timezone.now().isoformat()
                        })
                    else:
                        # Start new question
                        session.question_started_at = timezone.now()
                        session.save()

                        # Get new current question
                        current_question = questions[session.current_question_index]
                        question_start_time = session.question_started_at
                        time_left = 20  # Fresh timer for new question
                        auto_advanced = True

                        # Reset response count for new question
                        responses_received = 0

                        logger.info(f"✅ Auto-advanced to question {session.current_question_index + 1}")

            # FIXED: Handle finished status properly
            elif session.status == 'finished' or session.current_question_index >= total_questions:
                if session.status != 'finished':
                    session.status = 'finished'
                    session.ended_at = timezone.now()
                    session.save()

                players = session.players.filter(is_active=True).order_by('-score', 'joined_at')
                return Response({
                    'session_id': session.id,
                    'status': 'finished',
                    'current_question_index': session.current_question_index,
                    'total_questions': total_questions,
                    'final_scores': PlayerSerializer(players, many=True).data,
                    'players': PlayerSerializer(players, many=True).data,  # Add this for compatibility
                    'player_count': players.count(),  # Add this
                    'server_time': timezone.now().isoformat()
                })

            # Get active players with scores and response status
            players = session.players.filter(is_active=True).order_by('-score', 'joined_at')

            # ENHANCED: Add response status to each player
            players_data = []
            for player in players:
                player_data = PlayerSerializer(player).data

                # Check if this player has answered the current question
                if current_question:
                    has_answered = PlayerAnswer.objects.filter(
                        player=player,
                        question=current_question
                    ).exists()
                    player_data['has_answered'] = has_answered
                else:
                    player_data['has_answered'] = False

                players_data.append(player_data)

            response_data = {
                'session_id': session.id,
                'status': session.status,
                'current_question_index': session.current_question_index,
                'total_questions': total_questions,
                'time_left': round(time_left, 1),
                'question_start_time': question_start_time.isoformat() if question_start_time else None,
                'current_question': QuestionSerializer(current_question).data if current_question else None,
                'players': players_data,
                'player_count': players.count(),
                'responses_received': responses_received,  # FIXED: Add response count
                'server_time': timezone.now().isoformat(),
                'auto_advanced': auto_advanced
            }

            return Response(response_data)

        except GameSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


    @action(detail=True, methods=['post'])
    def start_game(self, request, pk=None):
        """Start the game (host only) - UPDATED WITH TIMING"""
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

        # Start the game with precise timing
        session.status = 'active'
        session.started_at = timezone.now()
        session.current_question_index = 0
        session.question_started_at = timezone.now()  # ADD THIS LINE
        session.save()

        # Get first question
        first_question = session.quiz.questions.first()

        return Response({
            'status': 'Game started',
            'current_question': QuestionSerializer(first_question).data if first_question else None,
            'question_started_at': timezone.now().isoformat(),
            'server_time': timezone.now().isoformat()
        })

    @action(detail=True, methods=['post'])
    def next_question(self, request, pk=None):
        """Move to the next question (host only) """
        session = self.get_object()

        # Check if user is the host
        if request.user != session.quiz.host:
            return Response(
                {'error': 'Only the host can control questions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get current state to avoid race conditions
        total_questions = session.quiz.questions.count()

        # If already at or past the last question, don't advance further
        if session.current_question_index >= total_questions - 1:
            # Mark as finished
            session.status = 'finished'
            session.ended_at = timezone.now()
            session.save()

            # Return final results
            players = session.players.filter(is_active=True).order_by('-score', 'joined_at')
            return Response({
                'status': 'Quiz completed',
                'final_scores': PlayerSerializer(players, many=True).data
            })

        # Increment question index
        session.current_question_index += 1

        # Check if quiz is complete after increment
        if session.current_question_index >= total_questions:
            session.status = 'finished'
            session.ended_at = timezone.now()
            session.save()

            # Return final results
            players = session.players.filter(is_active=True).order_by('-score', 'joined_at')
            return Response({
                'status': 'Quiz completed',
                'final_scores': PlayerSerializer(players, many=True).data
            })

        # Set new question start time - CRITICAL FOR SYNC!
        session.question_started_at = timezone.now()
        session.save()

        # Get current question
        current_question = session.quiz.questions.all().order_by('order')[session.current_question_index]

        logger.info(f"🎮 Host manually advanced to question {session.current_question_index + 1}")

        return Response({
            'current_question': QuestionSerializer(current_question).data,
            'question_number': session.current_question_index + 1,
            'total_questions': total_questions,
            'question_started_at': timezone.now().isoformat(),
            'server_time': timezone.now().isoformat(),
            'manually_advanced': True  # NEW: Flag to indicate manual advance
        })

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """Get current leaderboard"""
        print(f"LEADERBOARD REQUEST for session: {pk}")  # Debug log

        try:
            # Make sure we get the session correctly
            session = self.get_object()
            print(f"LEADERBOARD SESSION FOUND: {session.id} for quiz {session.quiz.title}")  # Debug log

            # Get players with explicit filtering
            players = session.players.filter(is_active=True).order_by('-score', 'joined_at')
            print(f"LEADERBOARD PLAYERS FOUND: {players.count()}")  # Debug log

            # Log each player for debugging
            for player in players:
                print(f"  PLAYER: {player.nickname}, Score: {player.score}, Active: {player.is_active}")

            response_data = {
                'leaderboard': PlayerSerializer(players, many=True).data,
                'session_status': session.status,
                'session_id': session.id,
                'quiz_title': session.quiz.title,
                'total_players': players.count()
            }

            print(f"LEADERBOARD RESPONSE: {response_data}")  # Debug log
            return Response(response_data)

        except GameSession.DoesNotExist:
            print(f"LEADERBOARD ERROR: Session {pk} does not exist")  # Debug log
            return Response(
                {'error': f'Session {pk} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"LEADERBOARD ERROR: {str(e)}")  # Debug log
            return Response(
                {'error': f'Server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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

    # ADD THESE FUNCTIONS TO THE END OF YOUR quiz_api/views.py FILE

    @api_view(['GET'])
    def user_quizzes(request):
        """Get current user's quizzes - Fixed function"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        quizzes = Quiz.objects.filter(host=request.user).order_by('-created_at')
        serializer = QuizSerializer(quizzes, many=True)

        logger.info(f"User {request.user.username} requested {quizzes.count()} quizzes")

        return Response({
            'results': serializer.data,
            'count': quizzes.count()
        })

    @api_view(['GET'])
    def get_current_question(request, pk):
        """Get current question for a session - Fixed function"""
        try:
            session = GameSession.objects.get(pk=pk)
            logger.info(f"Getting current question for session {session.id}, status: {session.status}")

            if session.status == 'waiting':
                return Response({
                    'session_id': session.id,
                    'status': 'waiting',
                    'message': 'Game has not started yet'
                })

            if session.status == 'finished':
                return Response({
                    'session_id': session.id,
                    'status': 'finished',
                    'message': 'Game has ended'
                })

            # Get current question
            questions = session.quiz.questions.all().order_by('order')
            total_questions = questions.count()

            if session.current_question_index < total_questions:
                current_question = questions[session.current_question_index]

                return Response({
                    'session_id': session.id,
                    'question': QuestionSerializer(current_question).data,
                    'question_number': session.current_question_index + 1,
                    'total_questions': total_questions,
                    'status': session.status
                })
            else:
                # Quiz completed
                session.status = 'finished'
                session.ended_at = timezone.now()
                session.save()

                return Response({
                    'session_id': session.id,
                    'status': 'finished',
                    'message': 'Quiz completed'
                })

        except GameSession.DoesNotExist:
            logger.error(f"Session {pk} not found")
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# Add test endpoint for debugging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


@csrf_exempt
@require_http_methods(["POST"])
def test_ai_service(request):
    """Test endpoint to debug AI question generation"""
    try:
        data = json.loads(request.body)
        topic = data.get('topic', 'Science')
        difficulty = data.get('difficulty', 'medium')

        logger.info(f"Testing AI service with topic: {topic}, difficulty: {difficulty}")

        ai_service = QuizAIService()

        # Test the AI service
        questions = ai_service.generate_quiz_questions(
            topic=topic,
            difficulty=difficulty,
            num_questions=3  # Test with fewer questions
        )

        return JsonResponse({
            'success': True,
            'topic': topic,
            'difficulty': difficulty,
            'questions_generated': len(questions),
            'questions': questions,
            'api_key_configured': bool(ai_service.api_key),
            'model_used': ai_service.model
        })

    except Exception as e:
        logger.error(f"AI service test error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

