# Generated manually for PaymentTransaction model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0009_foodbank_profile_extensions'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_payment_intent_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('stripe_session_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('payment_method', models.CharField(choices=[('credit_card', 'Credit Card'), ('mpesa', 'M-Pesa'), ('bank_transfer', 'Bank Transfer'), ('cash', 'Cash')], default='credit_card', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='KES', max_length=3)),
                ('transaction_fee', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('net_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('stripe_response', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('donation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment_transaction', to='authentication.donation')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
