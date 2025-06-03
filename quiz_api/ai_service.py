import requests
import json
import logging
from decouple import config
from typing import List, Dict

logger = logging.getLogger(__name__)


class QuizAIService:
    """Service for generating quiz questions using OpenRouter AI"""

    def __init__(self):
        self.api_key = config('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "microsoft/phi-4-reasoning-plus:free"

    def generate_quiz_questions(self, topic: str, difficulty: str = 'medium',
                                num_questions: int = 10) -> List[Dict]:
        """
        Generate quiz questions using AI

        Args:
            topic: The topic for the quiz
            difficulty: easy, medium, or hard
            num_questions: Number of questions to generate

        Returns:
            List of question dictionaries
        """

        # Construct the prompt
        prompt = self._create_prompt(topic, difficulty, num_questions)

        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a trivia quiz master who creates engaging, accurate, and fun questions. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            # Make the API request
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            # Parse the response
            result = response.json()
            content = result['choices'][0]['message']['content']

            # Extract JSON from the response
            questions = self._parse_ai_response(content)

            # Validate the questions
            validated_questions = self._validate_questions(questions)

            return validated_questions

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise Exception(f"Failed to generate questions: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise

    def _create_prompt(self, topic: str, difficulty: str, num_questions: int) -> str:
        """Create the prompt for the AI"""

        difficulty_guidelines = {
            'easy': 'Make questions suitable for beginners with basic knowledge',
            'medium': 'Make questions challenging but accessible to general audiences',
            'hard': 'Make questions difficult, requiring deep knowledge or critical thinking'
        }

        return f"""
        Create exactly {num_questions} trivia questions about "{topic}".

        Difficulty level: {difficulty} - {difficulty_guidelines.get(difficulty, '')}

        Requirements:
        1. Questions should be interesting and engaging
        2. Include a mix of different question types
        3. Ensure factual accuracy
        4. Make wrong answers plausible but clearly incorrect

        Return the response as a JSON array with this EXACT format:
        [
            {{
                "question": "The question text here",
                "correct_answer": "The correct answer",
                "wrong_answers": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"]
            }}
        ]

        Important: Return ONLY the JSON array, no additional text or formatting.
        """

    def _parse_ai_response(self, content: str) -> List[Dict]:
        """Parse the AI response to extract questions"""

        # Try to find JSON in the response
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]

        # Parse JSON
        try:
            questions = json.loads(content)
            return questions
        except json.JSONDecodeError:
            # Try to extract JSON from the content
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)

            raise ValueError("Could not parse AI response as JSON")

    def _validate_questions(self, questions: List[Dict]) -> List[Dict]:
        """Validate and clean the generated questions"""

        validated = []

        for q in questions:
            # Check required fields
            if not all(key in q for key in ['question', 'correct_answer', 'wrong_answers']):
                continue

            # Validate wrong_answers is a list with 3 items
            if not isinstance(q['wrong_answers'], list) or len(q['wrong_answers']) != 3:
                continue

            # Clean up the question
            validated_q = {
                'question': str(q['question']).strip(),
                'correct_answer': str(q['correct_answer']).strip(),
                'wrong_answers': [str(ans).strip() for ans in q['wrong_answers']]
            }

            # Skip if any field is empty
            if not validated_q['question'] or not validated_q['correct_answer']:
                continue

            if any(not ans for ans in validated_q['wrong_answers']):
                continue

            validated.append(validated_q)

        return validated

    def generate_sample_questions(self, topic: str, difficulty: str = 'medium') -> List[Dict]:
        """Generate sample questions for testing without API calls"""

        sample_questions = {
            'easy': [
                {
                    'question': f'What is the capital of {topic}?',
                    'correct_answer': 'Sample Capital',
                    'wrong_answers': ['Wrong City 1', 'Wrong City 2', 'Wrong City 3']
                },
                {
                    'question': f'True or False: {topic} is located in Europe?',
                    'correct_answer': 'True',
                    'wrong_answers': ['False', 'Sometimes', 'It depends']
                }
            ],
            'medium': [
                {
                    'question': f'Which year was {topic} established?',
                    'correct_answer': '1900',
                    'wrong_answers': ['1850', '1925', '1975']
                },
                {
                    'question': f'What is {topic} most famous for?',
                    'correct_answer': 'Its culture',
                    'wrong_answers': ['Its beaches', 'Its mountains', 'Its deserts']
                }
            ],
            'hard': [
                {
                    'question': f'What percentage of global production does {topic} represent?',
                    'correct_answer': '23%',
                    'wrong_answers': ['15%', '31%', '42%']
                },
                {
                    'question': f'Which historical figure is most associated with {topic}?',
                    'correct_answer': 'Historical Figure A',
                    'wrong_answers': ['Historical Figure B', 'Historical Figure C', 'Historical Figure D']
                }
            ]
        }

        return sample_questions.get(difficulty, sample_questions['medium'])[:10]