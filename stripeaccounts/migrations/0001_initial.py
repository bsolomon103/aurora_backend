# Generated by Django 4.1.7 on 2023-06-20 10:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('aurora_api', '0023_customer_mappings'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_description', models.CharField(max_length=140)),
                ('mcc', models.CharField(max_length=5)),
                ('phone', models.CharField(max_length=13)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aurora_api.customer')),
            ],
        ),
    ]