from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.utils import timezone


def fmt_dt(dt) -> str:
    if not dt:
        return "N/A"
    return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M")


def fmt_money(value) -> str:
    if value is None or value == "":
        return "N/A"
    try:
        d = Decimal(str(value))
    except Exception:
        return str(value)
    return f"{d:,.2f}"


def fmt_qty(quantity, unit: Optional[str]) -> str:
    if quantity is None or quantity == "":
        return "N/A"
    if unit:
        return f"{quantity} {unit}"
    return str(quantity)


def donation_item_desc(donation) -> str:
    # Keep the same item/description selection across CSV/PDF/Excel
    return (
        donation.item_name
        or donation.subsidized_product_type
        or donation.csr_description
        or donation.other_description
        or "N/A"
    )


def donation_qty_display(donation) -> str:
    if donation.quantity:
        return fmt_qty(donation.quantity, donation.quantity_unit)
    if donation.subsidized_quantity:
        return fmt_qty(donation.subsidized_quantity, donation.subsidized_quantity_unit)
    return "N/A"


def donation_amount_display(donation) -> str:
    if donation.amount:
        return fmt_money(donation.amount)
    if donation.subsidized_price:
        return fmt_money(donation.subsidized_price)
    return "N/A"

