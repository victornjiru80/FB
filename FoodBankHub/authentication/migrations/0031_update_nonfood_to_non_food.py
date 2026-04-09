# Generated manually to update 'nonfood' to 'non_food'

from django.db import migrations


def update_nonfood_to_non_food(apps, schema_editor):
    """Update all 'nonfood' values to 'non_food' in FoodBankRequest model"""
    FoodBankRequest = apps.get_model('authentication', 'FoodBankRequest')
    
    # Update all FoodBankRequest records with 'nonfood' to 'non_food'
    updated_count = FoodBankRequest.objects.filter(donation_type='nonfood').update(donation_type='non_food')
    
    if updated_count > 0:
        print(f"Updated {updated_count} FoodBankRequest records from 'nonfood' to 'non_food'")


def reverse_update(apps, schema_editor):
    """Reverse migration: update 'non_food' back to 'nonfood'"""
    FoodBankRequest = apps.get_model('authentication', 'FoodBankRequest')
    
    # Reverse the update
    FoodBankRequest.objects.filter(donation_type='non_food').update(donation_type='nonfood')


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0030_donation_csr_description_donation_csr_subcategory_and_more'),
    ]

    operations = [
        migrations.RunPython(update_nonfood_to_non_food, reverse_update),
    ]
