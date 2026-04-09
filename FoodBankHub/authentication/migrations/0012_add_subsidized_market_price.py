# Generated manually for adding subsidized_market_price field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_subsidized_goods_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='subsidized_market_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Original market price before discount', max_digits=10, null=True),
        ),
    ]
