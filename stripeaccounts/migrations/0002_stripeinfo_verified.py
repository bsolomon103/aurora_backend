# Generated by Django 4.1.7 on 2023-06-20 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stripeaccounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripeinfo',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
