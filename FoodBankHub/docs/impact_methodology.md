# Environmental Impact Methodology (Wingu / FoodBankHub)

This document defines a **defensible, data-driven methodology** for the Admin **Environmental Impact** dashboard and its exports.

It is designed to be:
- **Grounded in the data you already collect** (donations, allocations, requests, delivery status)
- **Consistent across formats** (dashboard, PDF, Excel/XLSX, PPTX, PNG)
- **Transparent** (every metric lists its required inputs and assumptions)

---

## 1) Current implementation (baseline) — what the code does today

### 1.1 Source files and where calculations happen

- **Core helpers (current constants + formulas)**: `FoodBankHub/FoodBankHub/custom_admin/impact_calculations.py`
- **Dashboard calculations and exports**: `FoodBankHub/FoodBankHub/custom_admin/views_impact.py`
- **Legacy Environmental Reports PDF export**: `FoodBankHub/FoodBankHub/custom_admin/environmental_exports.py`
- **Dashboard template & client-side “Excel Data” (CSV) export**: `FoodBankHub/FoodBankHub/custom_admin/templates/custom_admin/environmental_impact.html`

### 1.2 Current “environmental” assumptions (hardcoded)

From `custom_admin/impact_calculations.py`:

- **Food waste prevented (kg)**:
  - Free food: \(waste\_kg = quantity \times 1.0\)
  - Subsidized food: \(waste\_kg = subsidized\_quantity \times 0.8\)
- **CO₂ saved (tons)**:
  - \(co2\_tons = (waste\_kg \times 2.5) / 1000\)
- **Non-food impact (treated as kg-equivalent waste prevented)**:
  - Free non-food: \(waste\_kg = quantity \times 1.0\)
  - Subsidized non-food: \(waste\_kg = subsidized\_quantity \times 0.7\)
  - \(co2\_tons = (waste\_kg \times 2.0) / 1000\)

From `custom_admin/views_impact.py`:

- **Meals provided (estimate)**:
  - Assumption: **1 meal = 0.5 kg food**
  - \(meals = food\_waste\_prevented\_kg / 0.5\)
- **Estimated beneficiaries**:
  - \(unique\_recipients = distinct(DonationAllocation.recipient)\) within time window
  - Assumption: **avg_family_size = 4**
  - \(estimated\_beneficiaries = unique\_recipients \times 4\)
- **Equivalents**:
  - Trees: \(trees = total\_co2\_tons \times 1000 / 21\) (21 kg CO₂ per tree-year)
  - Cars: \(cars = total\_co2\_tons / 4.6\)
  - Homes: \(homes = total\_co2\_tons / 7.5\)

### 1.3 Current data inputs used (actual models/fields)

#### Donations (primary source)
Model: `authentication.models.Donation`

Used fields:
- Classification: `donation_type`, `donation_category`, `donation_mode`, `csr_subcategory`
- “Quantity” inputs: `quantity`, `subsidized_quantity`
- Money: `amount`
- Dates/filters: `donated_at`, `status`, `delivery_status`
- Attribution/grouping: `donor`, `foodbank`, `foodbank_request`, `request_management`

#### Allocations (social impact)
Model: `authentication.models.DonationAllocation`

Used fields:
- `allocated_at`
- `recipient` (distinct count)
- (Not consistently used today, but important): `declined_by_recipient`

#### “Posted donations” workflow tables (dashboard top cards)
Models used to build the “completed posted donations” subset:
- `UnspecifiedDonationManagement` (recipient_status == received)
- `Donation` (subsidized, accepted, delivered)
- `RequestManagement` (fulfilled/acknowledged) linked to delivered Donation
- `DonationResponse` (notes)

### 1.4 Current inconsistencies and risks

#### A) Dashboard top cards vs exports count different populations
The dashboard top cards show totals “From completed posted donations”, while some exports use **all accepted donations** in the time window.

**Impact**: totals can differ between:
- On-screen summary
- PDF/PPTX/PNG export
- Excel/XLSX export

#### B) Units are assumed (quantity treated as kg/units)
The current method effectively treats:
- `Donation.quantity` as “kg” (for food free) or “units” (for non-food)
- without checking `Donation.quantity_unit` (which exists and is not strictly standardized)

**Impact**: results can be nonsensical if donors enter “bags”, “boxes”, “pieces”, etc.

#### C) Template “methodology” text can drift from code
Some methodology text in templates does not strictly match the actual constants in `impact_calculations.py`.

---

## 2) Canonical definitions (the improved, consistent methodology)

This section defines **canonical variables** and **counting rules** so every report uses the same meaning.

### 2.1 Counting rules (what counts as “impact realized”)

Define three levels:

1) **Pledged** (donation created):
- `Donation` exists (any status)

2) **Accepted** (confirmed by foodbank/admin):
- `Donation.status == 'accepted'`

3) **Delivered/Received** (impact realized for environmental metrics):
- For item donations, preferred rule is:
  - `Donation.status == 'accepted'` AND `Donation.delivery_status == 'delivered'`
- For allocations, preferred rule is:
  - allocation exists and is not declined:
  - `DonationAllocation.declined_by_recipient == False`

**Recommendation**: Environmental metrics (waste prevented / CO₂) should use **Delivered/Received** by default, because that best reflects real-world diversion and avoids counting cancellations.

#### 2.1.1 Time window rules

All dashboards and exports must use the same definition of a “period”.

Recommended default (matches existing UI):
- `days` parameter (e.g., 30/90/180/365)
- `start_date = now - timedelta(days=days)`

Canonical filters by metric type:
- **Donation-scoped metrics** (food kg, waste, CO₂, money totals): use `Donation.donated_at >= start_date`
- **Allocation-scoped metrics** (unique recipients): use `DonationAllocation.allocated_at >= start_date`

If you need strict consistency, you can anchor everything to the same timestamp type (e.g., donation date only), but that can undercount recipients whose allocation happens later than the donation.

### 2.2 Canonical variables (names, units, sources)

| Variable | Unit | Definition | Primary source |
|---|---:|---|---|
| `donations_count` | count | Number of donations in scope | `Donation` |
| `food_kg_delivered` | kg | Total delivered food mass | `Donation` + item catalog conversion |
| `non_food_units_delivered` | units | Total delivered non-food items (unit-based) | `Donation` |
| `food_waste_prevented_kg` | kg | Food diverted from waste stream (proxy) | derived |
| `co2_saved_tons` | tons CO₂e | CO₂e avoided due to prevented waste | derived |
| `meals_provided` | meals | Meals delivered from food | derived |
| `unique_recipients_helped` | count | Distinct recipients receiving allocations (not declined) | `DonationAllocation` |
| `estimated_beneficiaries` | people | `unique_recipients_helped * avg_household_size` | derived |
| `monetary_amount_total` | KES | Total monetary donations accepted/paid | `Donation.amount` + optional `PaymentTransaction` |
| `meals_funded` | meals | Meals estimated from monetary donations | derived |
| `subsidy_value_total` | KES | Market-value minus paid for subsidized donations | `Donation.subsidized_market_price`, `subsidized_price` |

### 2.3 Environmental metrics scope (per your requirement)

You selected: **monetary/subsidized money does not contribute to environmental waste/CO₂ metrics**.

Therefore:
- **Environmental**: computed from **food items delivered** only (and optionally non-food as a separate “resource diversion” metric).
- **Social/Economic**: computed from food + money + subsidy value.

---

## 3) Item catalog approach (required to make metrics meaningful)

Because the project collects `Donation.item_name`, `Donation.quantity`, and `Donation.quantity_unit`, environmental metrics are only defensible if we normalize to **kg**.

### 3.1 Catalog schema (minimal viable)

Store a catalog keyed by `item_key` (normalized from `item_name`):

| Field | Type | Meaning |
|---|---|---|
| `item_key` | string | normalized identifier (e.g., `maize_flour`, `rice`) |
| `display_name` | string | human-friendly name |
| `category` | enum | `food` or `non_food` |
| `kg_per_unit` | float | if quantity unit is “unit-like” (bag/box/piece), default kg per 1 unit |
| `servings_per_kg` | float | for meals conversion; optional if using kg_per_meal instead |
| `aliases` | list[string] | alternative names to map raw inputs → item_key |
| `unit_conversions` | dict | optional: `{ "bag": 25, "box": 10 }` as kg per unit label |

### 3.2 Resolution rules (how raw donation data maps to catalog)

1) Normalize `Donation.item_name`:
   - lowercase, strip punctuation, collapse spaces
2) Map to `item_key` using:
   - exact alias match first
   - then fallback heuristics (contains keywords)
3) Normalize `Donation.quantity_unit`:
   - mass units: `kg`, `g`, `ton`, etc.
   - unit-like: `bag`, `box`, `piece`, etc. → use catalog’s `unit_conversions` or `kg_per_unit`
4) If conversion is not possible:
   - mark as `unknown_weight` and exclude from environmental totals (but still count as donation activity)

### 3.4 Normalization algorithm (pseudo-spec)

For each `Donation` in-scope:

1) Determine if donation contributes to **food mass**:
   - include if `donation_category == 'food'` and donation is in Delivered/Received scope
2) Resolve `item_key`:
   - if `item_name` is empty → `item_key = unknown`
   - else normalize string and match against catalog `aliases`
3) Resolve quantity unit:
   - if `quantity_unit` is a mass unit (`kg`, `g`, `ton`): convert to kg directly
   - else if `item_key` found and catalog has `unit_conversions[quantity_unit]`: use it
   - else if `item_key` found and catalog has `kg_per_unit`: use it
   - else set `unknown_weight = True`
4) Accumulate:
   - `food_kg_delivered += donation_food_kg` when not unknown
   - always increment `donations_count` for visibility, even when unknown

Outputs per donation row (useful for debugging/admin review):
- `item_key`, `raw_item_name`, `raw_quantity`, `raw_unit`, `converted_kg`, `unknown_weight_reason`

### 3.3 Example catalog entries (illustrative)

These examples show the shape of what we need, not final values:

| item_key | display_name | category | kg_per_unit | servings_per_kg | aliases (examples) |
|---|---|---|---:|---:|---|
| `maize_flour` | Maize flour | food | 2.0 | 8 | `unga`, `maize meal`, `posho` |
| `rice` | Rice | food | 1.0 | 6 | `basmati`, `pishori` |
| `beans` | Beans | food | 1.0 | 7 | `ndengu`, `green grams` |
| `cooking_oil` | Cooking oil | food | 0.9 | 0 | `oil`, `vegetable oil` |

Notes:
- `servings_per_kg` can be `0`/unset for items where you’d rather use a global `kg_per_meal` approach.
- If donors frequently use `bags/boxes`, add `unit_conversions` like `{ "bag": 25, "box": 10 }` per item.

---

## 4) Proposed formulas (canonical)

### 4.1 Food mass delivered

For each qualifying donation (Delivered/Received scope):

1) Convert to kg:
   - If `quantity_unit` is mass-convertible: convert directly
   - Else use item catalog conversion

Then:
- `food_kg_delivered = Σ donation_food_kg`

### 4.2 Food waste prevented (kg)

Define a single factor (configurable):
- `waste_diversion_factor_food = 1.0` (default)

Then:
- `food_waste_prevented_kg = food_kg_delivered * waste_diversion_factor_food`

> Note: The current code uses 1.0 and 0.8 based on “mode”. Under the improved method, the “mode” (free/subsidized) should not change physical waste diversion; instead, any discounting should be part of **economic** reporting. If you want to keep a policy discount for subsidized goods, document it here explicitly with justification.

### 4.3 CO₂ saved (tons CO₂e)

Define a single factor (configurable):
- `kgco2e_per_kg_food_waste = 2.5` (current baseline)

Then:
- `co2_saved_tons = (food_waste_prevented_kg * kgco2e_per_kg_food_waste) / 1000`

### 4.4 Meals provided

Two supported approaches (pick one and keep it consistent everywhere):

**Option A (simple, global constant)**:
- `kg_per_meal = 0.5` (current baseline)
- `meals_provided = food_kg_delivered / kg_per_meal`

**Option B (item-specific servings)**:
- `meals_provided = Σ (donation_food_kg * servings_per_kg(item_key))`

Recommendation: start with **Option A**, then migrate to Option B once the item catalog is populated.

### 4.5 Unique recipients and estimated beneficiaries

- `unique_recipients_helped = count(distinct DonationAllocation.recipient)`
  - Scope: allocations in the time window
  - Filter: exclude declined allocations (`declined_by_recipient=True`)
- `avg_household_size = 4` (current baseline)
- `estimated_beneficiaries = unique_recipients_helped * avg_household_size`

### 4.6 Monetary donations (social/economic only)

Per requirement, money should **not** affect `food_waste_prevented_kg` or `co2_saved_tons`.

Define:
- `monetary_amount_total = Σ Donation.amount` (where `donation_category='monetary'` and in-scope)

Optional stronger rule (if you want “paid” only):
- Use `PaymentTransaction.status == 'completed'` and sum `PaymentTransaction.amount` instead of `Donation.amount`.

Meals funded from money (explicit assumption required):
- `kes_per_meal` (e.g., 50–150 KES/meal depending on your program)
- `meals_funded = floor(monetary_amount_total / kes_per_meal)`

### 4.7 Subsidized donations (economic only; physical impact from delivered goods)

Subsidized donations often have both:
- a **physical quantity** (`subsidized_quantity`, `subsidized_quantity_unit`) and
- an **economic discount** (`subsidized_market_price`, `subsidized_price`)

Rules:
- Physical delivered food still contributes to `food_kg_delivered` (via item catalog conversion).
- Environmental metrics are derived from `food_kg_delivered` only (not from price).

Economic subsidy value:
- `subsidy_value_total = Σ max(subsidized_market_price - subsidized_price, 0)` (per donation)

---

## 5) Report outputs (single source of truth)

All exports and on-screen metrics should use the same output field names and units:

### 5.1 Executive summary fields

| Field | Unit |
|---|---:|
| `donations_count` | count |
| `food_kg_delivered` | kg |
| `food_waste_prevented_kg` | kg |
| `co2_saved_tons` | tons CO₂e |
| `meals_provided` | meals |
| `unique_recipients_helped` | count |
| `estimated_beneficiaries` | people |
| `monetary_amount_total` | KES |
| `meals_funded` | meals |
| `subsidy_value_total` | KES |

### 5.2 Attribution / breakdown fields (optional but recommended)

Breakdowns should be consistent by:
- donation category: `food`, `non_food`, `monetary`, `csr`, `other`
- donation mode: `free`, `subsidized`, `csr`, `discussion`
- organization: `foodbank`, `donor`
- workflow status: `pledged`, `accepted`, `delivered`

---

## 6) Implementation notes (how this maps to the current code)

### 6.1 What must change to align dashboard + exports

1) **Unify population**:
   - Dashboard top cards and all exports must use the **same scope** (accepted vs delivered vs posted-completed subset).
2) **Normalize units**:
   - Stop treating `Donation.quantity` as kg by default.
   - Convert using the **item catalog** + `quantity_unit`.
3) **Separate environmental vs economic**:
   - Keep money/subsidy out of waste/CO₂.

### 6.2 Where to plug in the new “normalization layer”

Ideal: a single module that computes canonical variables (e.g., `food_kg_delivered`, `co2_saved_tons`) from raw rows.
Then `custom_admin/views_impact.py`, `custom_admin/environmental_exports.py`, and the posted-table exports all depend on that module.

---          

## 7) Known limitations with current data (and how we handle them)

### 7.1 Transport emissions cannot be computed reliably (yet)
      
We currently have:
- `delivery_method`, `delivery_status`, `pickup_time`
- `address`/`location` strings in profiles and requests
    
We do **not** have:
- distance, route, lat/lon, vehicle type, trip logs

Therefore: this methodology **excludes** transport emissions until the project captures structured trip data.

### 7.2 Inventory spoilage/waste is not tracked 

We do not currently record spoilage/expiry disposal events.
So “waste prevented” is a **proxy** derived from delivered food mass, not a measured diversion.
                          
---                                                                                      
  
## 8) Required constants (declare them once)
  
These must be defined centrally and referenced everywhere:

- `kgco2e_per_kg_food_waste` (baseline 2.5)
- `waste_diversion_factor_food` (baseline 1.0)
- `kg_per_meal` (baseline 0.5) OR servings-per-kg in item catalog
- `avg_household_size` (baseline 4)
- `kes_per_meal` (for meals funded from money; choose and document)

---                        
                  
## 9) Alignment checklist against current dashboard/exports

This section is used to ensure the implementation phase produces **matching values** across UI and downloads.  
      
### 9.1 Units and labels (must remain consistent)

- `food_kg_delivered`, `food_waste_prevented_kg`: **kg**
- `co2_saved_tons`: **tons CO₂e**
- `monetary_amount_total`: **KES**
- `meals_provided`, `meals_funded`: **count**
- `unique_recipients_helped`, `estimated_beneficiaries`: **count**

### 9.2 Population choice (must be a single rule)

Pick exactly one default population for the Environmental Impact page and all exports:
       
- **Option 1 (recommended)**: Delivered/Received scope
  - `Donation.status='accepted' AND delivery_status='delivered'`
  - allocations not declined
- **Option 2**: Accepted scope
  - `Donation.status='accepted'` (ignores delivery)
   
Current mismatch to fix during implementation:
- Dashboard top cards currently emphasize “completed posted donations” while exports may use all accepted donations.
        
### 9.3 “Excel Data” export type

The current “Excel Data” button on the dashboard generates **CSV** client-side.
If you want “real Excel” consistently, align it with the existing openpyxl `.xlsx` exporters used elsewhere.
              