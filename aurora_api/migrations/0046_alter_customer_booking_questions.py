# Generated by Django 4.1.7 on 2023-09-28 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0045_alter_treatments_treatment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='booking_questions',
            field=models.TextField(null=True),
        ),
    ]
