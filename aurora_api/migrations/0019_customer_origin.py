# Generated by Django 4.1.7 on 2023-06-12 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0018_remove_customer_client_secret_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='origin',
            field=models.CharField(max_length=200, null=True, unique=True),
        ),
    ]
