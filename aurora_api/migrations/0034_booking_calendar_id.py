# Generated by Django 4.1.7 on 2023-07-02 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0033_rename_status_booking_booking_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='calendar_id',
            field=models.CharField(default='', max_length=100),
        ),
    ]
