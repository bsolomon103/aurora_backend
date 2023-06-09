# Generated by Django 4.1.7 on 2023-06-14 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0019_customer_origin'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppCredentials',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('google_secret', models.FileField(null=True, unique=True, upload_to='secrets_file')),
            ],
        ),
        migrations.RemoveField(
            model_name='customer',
            name='client_secret_file',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='origin',
        ),
        migrations.RemoveField(
            model_name='models',
            name='smart_funnel',
        ),
        migrations.RemoveField(
            model_name='models',
            name='tokens',
        ),
    ]
