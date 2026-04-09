# Generated manually for M-Pesa integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0021_donation_discussion_status_and_more'),
    ]

    operations = [
        # Add M-Pesa phone field to Donation model
        migrations.AddField(
            model_name='donation',
            name='mpesa_phone',
            field=models.CharField(blank=True, help_text='M-Pesa phone number for monetary donations', max_length=12, null=True),
        ),
        
        # Add M-Pesa fields to PaymentTransaction model
        migrations.AddField(
            model_name='paymenttransaction',
            name='mpesa_checkout_request_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='mpesa_merchant_request_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='mpesa_receipt_number',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
