from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0077_backfill_foodbankrequest_deadline'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportMessageReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('is_from_admin', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='support_message_replies', to=settings.AUTH_USER_MODEL)),
                ('support_message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='authentication.supportmessage')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
