from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'total_quizzes_hosted',
                 'total_quizzes_played', 'created_at']
        read_only_fields = ['id', 'total_quizzes_hosted',
                          'total_quizzes_played', 'created_at']