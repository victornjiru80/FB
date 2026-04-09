"""
Legacy impact calculation helpers (kept for backwards compatibility).

New canonical implementation lives in:
- custom_admin/impact_normalization.py

Prefer using the canonical metrics builder for all new dashboard/export logic.
"""


def calculate_food_waste_prevented(free_food_kg, subsidized_food_kg):
    """
    Calculate food waste prevented based on donation types.
    Free Food: 1.0 kg per unit; Subsidized Food: 0.8 kg per unit.
    Returns: Total kg of food waste prevented.
    """
    food_waste_prevented = (free_food_kg * 1.0) + (subsidized_food_kg * 0.8)
    return round(food_waste_prevented, 2)


def calculate_co2_saved(food_waste_prevented_kg):
    """
    Calculate CO₂ saved based on food waste prevented.
    Formula: (FoodWastePrevented × 2.5) ÷ 1000 (tons).
    """
    co2_saved_tons = (food_waste_prevented_kg * 2.5) / 1000
    return round(co2_saved_tons, 2)


def calculate_non_food_impact(free_non_food_units, subsidized_non_food_units):
    """
    Calculate non-food resource impact.
    Free Non-Food: 1.0; Subsidized Non-Food: 0.7. CO₂: waste × 2 / 1000 tons.
    Returns: dict with waste_prevented_kg and co2_saved_tons.
    """
    waste_prevented = (free_non_food_units * 1.0) + (subsidized_non_food_units * 0.7)
    co2_saved = (waste_prevented * 2) / 1000
    return {
        'waste_prevented_kg': round(waste_prevented, 2),
        'co2_saved_tons': round(co2_saved, 2)
    }


def get_donation_impact(donation):
    """
    Return waste prevented (kg) and CO₂ saved (tons) for a single Donation.
    Uses same rules as environmental reports: food free 1.0/subsidized 0.8,
    non_food via calculate_non_food_impact, others 0.
    Returns: dict with waste_prevented_kg and co2_saved_tons.
    """
    # Canonical: food-only environmental impact computed from normalized kg.
    # If the donation cannot be converted, impact is 0 (but should be flagged separately in diagnostics).
    from .impact_normalization import donation_to_food_kg

    category = getattr(donation, 'donation_category', None)
    waste_prevented_kg = 0.0
    co2_saved_tons = 0.0

    if category == 'food':
        norm = donation_to_food_kg(donation)
        if norm.converted_kg is not None:
            waste_prevented_kg = float(norm.converted_kg) * 1.0
            co2_saved_tons = (waste_prevented_kg * 2.5) / 1000.0

    return {
        'waste_prevented_kg': round(float(waste_prevented_kg or 0), 2),
        'co2_saved_tons': round(float(co2_saved_tons or 0), 3),
    }
