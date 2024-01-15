# Generated by Django 4.1.7 on 2024-01-12 09:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_api', '0053_chat_intent'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Booking',
        ),
        migrations.RemoveField(
            model_name='image',
            name='customer',
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
        migrations.RemoveField(
            model_name='price',
            name='product_seller',
        ),
        migrations.RemoveField(
            model_name='treatments',
            name='customer_name',
        ),
        migrations.RemoveField(
            model_name='treatmentseller',
            name='product',
        ),
        migrations.RemoveField(
            model_name='treatmentseller',
            name='seller',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='booking_questions',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='products',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='treatment_init',
        ),
        migrations.DeleteModel(
            name='Image',
        ),
        migrations.DeleteModel(
            name='Price',
        ),
        migrations.DeleteModel(
            name='Treatments',
        ),
        migrations.DeleteModel(
            name='TreatmentSeller',
        ),
    ]