# Generated by Django 4.1.7 on 2024-01-17 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0056_remove_chat_rating_chat_chats'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='human_agent',
            field=models.BooleanField(default=False),
        ),
    ]