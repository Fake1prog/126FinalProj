# Generated by Django 4.2.7 on 2025-06-05 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamesession',
            name='question_started_at',
            field=models.DateTimeField(blank=True, help_text='When the current question started', null=True),
        ),
    ]
