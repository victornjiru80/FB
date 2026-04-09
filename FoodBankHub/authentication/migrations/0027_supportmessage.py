# Generated manually for SupportMessage model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0026_foodbankrequest_linked_recipient_request_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=[('donation_help', 'Help with Donation Process'), ('payment_issue', 'Payment or Transaction Issues'), ('tax_receipt', 'Tax Receipt Questions'), ('request_management', 'Help with Request Management'), ('donation_processing', 'Donation Processing Issues'), ('analytics_reports', 'Analytics and Reports'), ('account_setup', 'Account Setup and Configuration'), ('recipient_communication', 'Recipient Communication'), ('training_resources', 'Training and Resources'), ('request_help', 'Help with My Request'), ('donation_inquiry', 'Donation Inquiry'), ('account_issue', 'Account Issues'), ('technical_support', 'Technical Support'), ('feedback', 'Feedback or Suggestions'), ('other', 'Other')], max_length=50)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('new', 'New'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='new', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('admin_response', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, limit_choices_to={'is_staff': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_support_messages', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Support Message',
                'verbose_name_plural': 'Support Messages',
                'ordering': ['-created_at'],
            },
        ),
    ]
