from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'total_quizzes_hosted',
                   'total_quizzes_played', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Quiz Statistics', {
            'fields': ('total_quizzes_hosted', 'total_quizzes_played')
        }),
    )