# Generated by Django 4.1.7 on 2023-04-28 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='models',
            name='process',
            field=models.JSONField(null=True),
        ),
    ]
