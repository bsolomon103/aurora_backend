# Generated by Django 4.1.7 on 2024-01-12 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0054_delete_booking_remove_image_customer_delete_payment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RateLimitSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255, unique=True)),
                ('limit', models.PositiveIntegerField()),
                ('interval', models.CharField(max_length=20)),
            ],
        ),
    ]