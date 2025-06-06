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
        # Updated to use the correct free model
        self.model = "deepseek/deepseek-chat-v3-0324:free"

        # Log API key status (but not the actual key)
        if self.api_key:
            logger.info(f"OpenRouter API key configured (length: {len(self.api_key)})")
        else:
            logger.error("OpenRouter API key not found in environment variables")

    def generate_quiz_questions(self, topic: str, difficulty: str = 'medium',
                                num_questions: int = 5) -> List[Dict]:
        """
        Generate quiz questions using AI

        Args:
            topic: The topic for the quiz
            difficulty: easy, medium, or hard
            num_questions: Number of questions to generate (default: 5)

        Returns:
            List of question dictionaries
        """

        logger.info(f"Generating {num_questions} {difficulty} questions about: {topic}")

        # Check if API key is available
        if not self.api_key:
            logger.error("No OpenRouter API key found, using fallback questions")
            return self.generate_sample_questions(topic, difficulty)

        # Construct the prompt
        prompt = self._create_prompt(topic, difficulty, num_questions)
        logger.info(f"Using AI model: {self.model}")

        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",  # Required for free tier
            "X-Title": "Quiz Platform"  # Optional, helps with tracking
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert quiz creator. You generate factual, accurate, and engaging multiple-choice questions on any topic. Always respond with valid JSON only, no extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }

        try:
            logger.info("Making API request to OpenRouter...")
            # Make the API request
            print(f"Headers: {headers}")
            print(f"Payload: {json.dumps(data, indent=2)}")  
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)

            logger.info(f"OpenRouter API response status: {response.status_code}")

            if response.status_code == 401:
                logger.error("OpenRouter API: Unauthorized - check your API key")
                return self.generate_sample_questions(topic, difficulty)
            elif response.status_code == 429:
                logger.error("OpenRouter API: Rate limit exceeded")
                return self.generate_sample_questions(topic, difficulty)
            elif response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return self.generate_sample_questions(topic, difficulty)

            response.raise_for_status()

            print(f"⬅️ Raw response: {response.text}")
            # Parse the response
            result = response.json()
            logger.info("Successfully received AI response")

            if 'choices' not in result or not result['choices']:
                logger.error("No choices in API response")
                return self.generate_sample_questions(topic, difficulty)

            content = result['choices'][0]['message']['content']
            logger.info(f"AI generated content length: {len(content)} characters")

            # Extract JSON from the response
            questions = self._parse_ai_response(content)
            logger.info(f"Parsed {len(questions)} questions from AI response")

            # Validate the questions
            validated_questions = self._validate_questions(questions)
            logger.info(f"Validated {len(validated_questions)} questions")

            if len(validated_questions) == 0:
                logger.warning("No valid questions generated by AI, using fallback")
                return self.generate_sample_questions(topic, difficulty)

            return validated_questions

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return self.generate_sample_questions(topic, difficulty)
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return self.generate_sample_questions(topic, difficulty)

    def _create_prompt(self, topic: str, difficulty: str, num_questions: int) -> str:
        """Create the prompt for the AI"""

        difficulty_guidelines = {
            'easy': 'Create basic questions suitable for beginners. Focus on fundamental facts and simple concepts.',
            'medium': 'Create moderately challenging questions that require some knowledge and understanding.',
            'hard': 'Create difficult questions that require deep knowledge, critical thinking, or specialized understanding.'
        }

        return f"""Create exactly {num_questions} multiple-choice trivia questions about "{topic}".

DIFFICULTY: {difficulty} - {difficulty_guidelines.get(difficulty, '')}

REQUIREMENTS:
1. Each question must be factually accurate and well-researched
2. Questions should be diverse and cover different aspects of {topic}
3. Each question needs exactly 3 wrong answers and 1 correct answer
4. Wrong answers should be plausible but clearly incorrect
5. Questions should be interesting and educational

RESPONSE FORMAT:
Return ONLY a JSON array with this exact structure:

[
    {{
        "question": "Clear, specific question about {topic}?",
        "correct_answer": "The factually correct answer",
        "wrong_answers": ["Plausible wrong answer 1", "Plausible wrong answer 2", "Plausible wrong answer 3"]
    }},
    {{
        "question": "Another question about {topic}?",
        "correct_answer": "Another correct answer",
        "wrong_answers": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"]
    }}
]

Generate {num_questions} questions about {topic} at {difficulty} difficulty level. Return ONLY the JSON array, no other text."""

    def _parse_ai_response(self, content: str) -> List[Dict]:
        """Parse the AI response to extract questions"""

        # Clean up the response
        content = content.strip()

        logger.info(f"Parsing AI response: {content[:200]}...")  # Log first 200 chars

        # Remove markdown code blocks if present
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]

        # Find JSON array in the content
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1

        if start_idx == -1 or end_idx == 0:
            logger.error("No JSON array found in AI response")
            raise ValueError("Could not find JSON array in AI response")

        json_str = content[start_idx:end_idx]
        logger.info(f"Extracted JSON: {json_str[:300]}...")  # Log first 300 chars

        try:
            questions = json.loads(json_str)
            logger.info(f"Successfully parsed JSON with {len(questions)} questions")
            return questions
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Failed JSON: {json_str}")
            raise ValueError(f"Could not parse AI response as JSON: {str(e)}")

    def _validate_questions(self, questions: List[Dict]) -> List[Dict]:
        """Validate and clean the generated questions"""

        if not isinstance(questions, list):
            logger.error("Questions is not a list")
            return []

        validated = []

        for i, q in enumerate(questions):
            logger.info(f"Validating question {i + 1}: {q}")

            # Check required fields
            if not all(key in q for key in ['question', 'correct_answer', 'wrong_answers']):
                logger.warning(f"Question {i + 1} missing required fields")
                continue

            # Validate wrong_answers is a list with 3 items
            if not isinstance(q['wrong_answers'], list) or len(q['wrong_answers']) != 3:
                logger.warning(f"Question {i + 1} has invalid wrong_answers")
                continue

            # Clean up the question
            validated_q = {
                'question': str(q['question']).strip(),
                'correct_answer': str(q['correct_answer']).strip(),
                'wrong_answers': [str(ans).strip() for ans in q['wrong_answers']]
            }

            # Skip if any field is empty
            if not validated_q['question'] or not validated_q['correct_answer']:
                logger.warning(f"Question {i + 1} has empty question or correct answer")
                continue

            if any(not ans for ans in validated_q['wrong_answers']):
                logger.warning(f"Question {i + 1} has empty wrong answers")
                continue

            logger.info(f"Question {i + 1} validated successfully")
            validated.append(validated_q)

        logger.info(f"Validation complete: {len(validated)} out of {len(questions)} questions passed")
        return validated

    def generate_sample_questions(self, topic: str, difficulty: str = 'medium') -> List[Dict]:
        """Generate sample questions for testing or when AI fails"""

        logger.warning(f"Using fallback sample questions for {topic} ({difficulty})")

        # Generate more realistic sample questions based on topic
        base_questions = [
            {
                'question': f'Which of the following is most commonly associated with {topic}?',
                'correct_answer': f'Historical significance of {topic}',
                'wrong_answers': ['Modern technology', 'Space exploration', 'Marine biology']
            },
            {
                'question': f'What time period is most relevant to {topic}?',
                'correct_answer': '20th century',
                'wrong_answers': ['Stone Age', 'Medieval period', 'Far future']
            },
            {
                'question': f'Which field of study would most likely research {topic}?',
                'correct_answer': 'Social sciences',
                'wrong_answers': ['Astronomy', 'Chemistry', 'Geology']
            },
            {
                'question': f'What is a key characteristic of {topic}?',
                'correct_answer': 'Cultural importance',
                'wrong_answers': ['Radioactivity', 'Magnetic properties', 'Gaseous state']
            },
            {
                'question': f'Where would you most likely encounter information about {topic}?',
                'correct_answer': 'Educational institutions',
                'wrong_answers': ['Underwater caves', 'Space stations', 'Arctic research stations']
            }
        ]

        return base_questions[:5]  # Return exactly 5 questions