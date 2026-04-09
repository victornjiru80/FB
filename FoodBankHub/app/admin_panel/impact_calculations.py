"""
Shared impact calculation helpers for environmental reports and PDF export.
Aligns with dashboard methodology (UNEP/WRAP benchmarks).
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
    category = getattr(donation, 'donation_category', None)
    mode = getattr(donation, 'donation_mode', None)
    quantity = getattr(donation, 'quantity', None) or 0
    subsidized_qty = getattr(donation, 'subsidized_quantity', None) or 0

    waste_prevented_kg = 0
    co2_saved_tons = 0

    if category == 'food':
        if mode == 'free':
            waste_prevented_kg = quantity * 1.0
        elif mode == 'subsidized':
            waste_prevented_kg = subsidized_qty * 0.8
        co2_saved_tons = (waste_prevented_kg * 2.5) / 1000
    elif category == 'non_food':
        free_units = quantity if mode == 'free' else 0
        sub_units = subsidized_qty if mode == 'subsidized' else 0
        impact = calculate_non_food_impact(free_units, sub_units)
        waste_prevented_kg = impact['waste_prevented_kg']
        co2_saved_tons = impact['co2_saved_tons']

    return {
        'waste_prevented_kg': round(waste_prevented_kg, 2),
        'co2_saved_tons': round(co2_saved_tons, 3),
    }
