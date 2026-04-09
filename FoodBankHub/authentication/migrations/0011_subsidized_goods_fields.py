# Generated manually for subsidized goods fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0010_paymenttransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='subsidized_product_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='donation',
            name='subsidized_quantity',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='donation',
            name='subsidized_quantity_unit',
            field=models.CharField(blank=True, choices=[('kg', 'Kilograms'), ('litres', 'Litres'), ('packets', 'Packets'), ('items', 'Items')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='donation',
            name='subsidized_discount_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
