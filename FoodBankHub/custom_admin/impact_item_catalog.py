"""
Lightweight per-item catalog used for impact normalization.

This is intentionally file-based (not DB-backed) to keep the first iteration
simple and auditable. It can be migrated to a model later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class ItemCatalogEntry:
    item_key: str
    display_name: str
    category: str  # "food" | "non_food"
    kg_per_unit: Optional[float] = None
    servings_per_kg: Optional[float] = None
    # unit_conversions maps arbitrary unit labels to kg-per-1-unit
    unit_conversions: Optional[Dict[str, float]] = None
    aliases: Optional[Iterable[str]] = None


def _norm(s: str) -> str:
    return " ".join((s or "").strip().lower().replace("_", " ").split())


# NOTE: Populate these gradually based on real `Donation.item_name` values.
# Values here are placeholders and should be reviewed programmatically later.
CATALOG: Dict[str, ItemCatalogEntry] = {
    "maize_flour": ItemCatalogEntry(
        item_key="maize_flour",
        display_name="Maize flour",
        category="food",
        kg_per_unit=2.0,
        servings_per_kg=8.0,
        unit_conversions={
            "kg": 1.0,
            "g": 0.001,
            "gram": 0.001,
            "grams": 0.001,
            "bag": 25.0,
        },
        aliases=["unga", "maize meal", "maize flour", "posho", "corn flour"],
    ),
    "rice": ItemCatalogEntry(
        item_key="rice",
        display_name="Rice",
        category="food",
        kg_per_unit=1.0,
        servings_per_kg=6.0,
        unit_conversions={"kg": 1.0, "g": 0.001, "bag": 25.0},
        aliases=["rice", "basmati", "pishori"],
    ),
    "beans": ItemCatalogEntry(
        item_key="beans",
        display_name="Beans",
        category="food",
        kg_per_unit=1.0,
        servings_per_kg=7.0,
        unit_conversions={"kg": 1.0, "g": 0.001, "bag": 25.0},
        aliases=["beans", "ndengu", "green grams", "mung", "mung beans"],
    ),
    "cooking_oil": ItemCatalogEntry(
        item_key="cooking_oil",
        display_name="Cooking oil",
        category="food",
        # Approx 0.91kg per liter, but donors may enter units inconsistently.
        kg_per_unit=0.9,
        servings_per_kg=None,
        unit_conversions={"l": 0.9, "liter": 0.9, "litre": 0.9, "ml": 0.0009, "kg": 1.0, "g": 0.001},
        aliases=["oil", "cooking oil", "vegetable oil"],
    ),
}


def resolve_item_key(raw_item_name: str) -> Optional[str]:
    needle = _norm(raw_item_name)
    if not needle:
        return None

    for key, entry in CATALOG.items():
        aliases = list(entry.aliases or [])
        aliases.append(entry.display_name)
        aliases.append(key)
        if any(_norm(a) == needle for a in aliases):
            return key

    # very small heuristic fallback
    for key, entry in CATALOG.items():
        if any(_norm(a) in needle for a in (entry.aliases or [])):
            return key

    return None

