"""
Canonical impact normalization and metric computation.

Implements the methodology described in docs/impact_methodology.md:
- Environmental metrics are computed from delivered/received FOOD quantities only.
- Monetary/subsidy values contribute to social/economic metrics only (not waste/CO₂).
- Quantity normalization uses a per-item catalog and unit conversion rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional, Tuple

from django.db.models import QuerySet

from .impact_item_catalog import CATALOG, resolve_item_key


MASS_UNITS = {
    "kg": 1.0,
    "kilogram": 1.0,
    "kilograms": 1.0,
    "g": 0.001,
    "gram": 0.001,
    "grams": 0.001,
    "ton": 1000.0,
    "tons": 1000.0,
    "tonne": 1000.0,
    "tonnes": 1000.0,
}


def _norm_unit(u: str) -> str:
    return (u or "").strip().lower()


@dataclass
class DonationNormalization:
    donation_id: int
    item_key: Optional[str]
    raw_item_name: str
    raw_quantity: float
    raw_unit: str
    converted_kg: Optional[float]
    unknown_weight_reason: str = ""


@dataclass
class ImpactMetrics:
    # time window
    days: int
    start_date: datetime

    # counts
    donations_count: int

    # environmental (food only)
    food_kg_delivered: float
    food_waste_prevented_kg: float
    co2_saved_tons: float
    meals_provided: int

    # social
    unique_recipients_helped: int
    estimated_beneficiaries: int

    # monetary/social-economic
    monetary_amount_total: Decimal
    meals_funded: int
    subsidy_value_total: Decimal

    # diagnostics
    unknown_weight_donations_count: int


def donation_to_food_kg(donation) -> DonationNormalization:
    """
    Convert a Donation's item quantity to kg for food impact accounting.
    Returns a DonationNormalization record.
    """
    donation_id = int(getattr(donation, "id", 0) or 0)
    raw_item_name = (getattr(donation, "item_name", "") or "").strip()
    raw_unit = (getattr(donation, "quantity_unit", "") or "").strip()
    raw_quantity = float(getattr(donation, "quantity", 0) or 0)

    item_key = resolve_item_key(raw_item_name)
    unit = _norm_unit(raw_unit)

    if raw_quantity <= 0:
        return DonationNormalization(
            donation_id=donation_id,
            item_key=item_key,
            raw_item_name=raw_item_name,
            raw_quantity=raw_quantity,
            raw_unit=raw_unit,
            converted_kg=None,
            unknown_weight_reason="quantity_missing_or_zero",
        )

    # direct mass conversion
    if unit in MASS_UNITS:
        return DonationNormalization(
            donation_id=donation_id,
            item_key=item_key,
            raw_item_name=raw_item_name,
            raw_quantity=raw_quantity,
            raw_unit=raw_unit,
            converted_kg=raw_quantity * MASS_UNITS[unit],
        )

    # catalog-based conversion
    if item_key and item_key in CATALOG:
        entry = CATALOG[item_key]
        conv = (entry.unit_conversions or {}).get(unit)
        if conv:
            return DonationNormalization(
                donation_id=donation_id,
                item_key=item_key,
                raw_item_name=raw_item_name,
                raw_quantity=raw_quantity,
                raw_unit=raw_unit,
                converted_kg=raw_quantity * float(conv),
            )
        if entry.kg_per_unit:
            return DonationNormalization(
                donation_id=donation_id,
                item_key=item_key,
                raw_item_name=raw_item_name,
                raw_quantity=raw_quantity,
                raw_unit=raw_unit,
                converted_kg=raw_quantity * float(entry.kg_per_unit),
            )

        return DonationNormalization(
            donation_id=donation_id,
            item_key=item_key,
            raw_item_name=raw_item_name,
            raw_quantity=raw_quantity,
            raw_unit=raw_unit,
            converted_kg=None,
            unknown_weight_reason="catalog_entry_missing_conversion",
        )

    return DonationNormalization(
        donation_id=donation_id,
        item_key=item_key,
        raw_item_name=raw_item_name,
        raw_quantity=raw_quantity,
        raw_unit=raw_unit,
        converted_kg=None,
        unknown_weight_reason="unknown_item_or_unit",
    )


def compute_impact_metrics(
    *,
    days: int,
    start_date: datetime,
    delivered_food_donations: Iterable,
    accepted_monetary_donations: Iterable,
    accepted_subsidized_donations: Iterable,
    unique_recipients_helped: int,
    avg_household_size: int = 4,
    kgco2e_per_kg_food_waste: float = 2.5,
    waste_diversion_factor_food: float = 1.0,
    kg_per_meal: float = 0.5,
    kes_per_meal: int = 100,
) -> Tuple[ImpactMetrics, list[DonationNormalization]]:
    """
    Build canonical metrics. Returns (ImpactMetrics, normalization_debug_rows).
    """
    delivered_food_donations = list(delivered_food_donations)
    accepted_monetary_donations = list(accepted_monetary_donations)
    accepted_subsidized_donations = list(accepted_subsidized_donations)

    debug_rows: list[DonationNormalization] = []

    food_kg_delivered = 0.0
    unknown_weight = 0

    for d in delivered_food_donations:
        norm = donation_to_food_kg(d)
        debug_rows.append(norm)
        if norm.converted_kg is None:
            unknown_weight += 1
            continue
        food_kg_delivered += float(norm.converted_kg)

    food_waste_prevented_kg = float(food_kg_delivered) * float(waste_diversion_factor_food)
    co2_saved_tons = (food_waste_prevented_kg * float(kgco2e_per_kg_food_waste)) / 1000.0
    meals_provided = int(food_kg_delivered / float(kg_per_meal)) if kg_per_meal else 0

    monetary_amount_total = sum((getattr(d, "amount", None) or Decimal("0")) for d in accepted_monetary_donations)

    # Subsidy value totals (economic only)
    subsidy_value_total = Decimal("0")
    for d in accepted_subsidized_donations:
        market = getattr(d, "subsidized_market_price", None)
        price = getattr(d, "subsidized_price", None)
        try:
            if market is not None and price is not None:
                diff = Decimal(market) - Decimal(price)
                if diff > 0:
                    subsidy_value_total += diff
        except Exception:
            # ignore malformed values
            pass

    meals_funded = int(monetary_amount_total / Decimal(kes_per_meal)) if kes_per_meal else 0
    estimated_beneficiaries = int(unique_recipients_helped * int(avg_household_size or 0))

    metrics = ImpactMetrics(
        days=int(days),
        start_date=start_date,
        donations_count=len(delivered_food_donations),
        food_kg_delivered=round(food_kg_delivered, 2),
        food_waste_prevented_kg=round(food_waste_prevented_kg, 2),
        co2_saved_tons=round(co2_saved_tons, 3),
        meals_provided=int(meals_provided),
        unique_recipients_helped=int(unique_recipients_helped),
        estimated_beneficiaries=int(estimated_beneficiaries),
        monetary_amount_total=monetary_amount_total,
        meals_funded=int(meals_funded),
        subsidy_value_total=subsidy_value_total,
        unknown_weight_donations_count=int(unknown_weight),
    )

    return metrics, debug_rows


def qs_iter(qs: QuerySet, chunk_size: int = 500):
    """
    Iterate a queryset in chunks without loading everything at once.
    """
    return qs.iterator(chunk_size=chunk_size)

