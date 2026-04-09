# FoodBankHub: Tech Stack, Architecture, and Learning Outline

## 1) Project Snapshot

FoodBankHub is a multi-role donation platform built with Django.  
It connects:
- donors
- foodbanks
- recipients
- platform admins

It supports:
- direct and request-based donations
- subsidized donations
- allocation workflows
- subscription/payment verification
- reports (PDF/CSV/Excel)
- custom admin operations

---

## 2) Languages and Technologies

### Core Languages
- Python (backend)
- HTML (Django templates)
- CSS
- JavaScript (vanilla JS in templates + static files)
- SQL (via Django ORM; SQLite now, PostgreSQL-ready)

### Backend Framework
- Django `5.2.7`
- Custom user model (`AUTH_USER_MODEL = authentication.CustomUser`)
- Role-based access and custom decorators/middleware

### Main Django Apps
- `authentication` (core domain and most business logic)
- `custom_admin` (separate admin portal, analytics, operations)
- `reports` (role-based reporting/export dashboards)

### Frontend/UI
- Bootstrap 5 (CDN)
- Font Awesome
- AOS (animations)
- Chart.js (analytics charts in dashboards)
- DataTables + jQuery (used in admin custom dashboard pages)

### Reporting / Export Libraries
- `reportlab` (PDF generation)
- `openpyxl` (Excel generation)
- CSV exports via Python stdlib `csv`

### Payment and External Integrations
- Stripe (`stripe` Python SDK)
- M-Pesa Daraja integration (`requests`-based service in `authentication/mpesa_utils.py`)

### Config / Environment
- `python-decouple` (`.env` driven settings)
- file/media uploads via Django `MEDIA_ROOT`

---

## 3) Database (PostgreSQL Position)

### Current Active DB
- SQLite is currently active in `FoodBankHub/settings.py`.

### PostgreSQL Readiness
- PostgreSQL config blocks already exist in settings (commented).
- There is a migration helper command:
  - `authentication/management/commands/migrate_sqlite_to_postgres.py`
- `.env` already includes PostgreSQL keys (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

### Important Note
- `requirements.txt` currently comments out psycopg:
  - `# psycopg==3.1.13`
- For PostgreSQL rollout, install/enable psycopg and switch DB engine in settings.

---

## 4) High-Level Architecture

### URL Layer
- Root router: `FoodBankHub/urls.py`
- Large route surface in `authentication/urls.py` (donations, requests, dashboards, payments, exports).
- Separate route namespaces:
  - `/admin/` -> custom admin app
  - `/reports/` -> reports app

### Request Handling Style
- Predominantly function-based views.
- Some class-based views for home/registration.
- Heavy server-rendered pages (Django templates), with JS for modals/actions.

### Security and Session Customization
- Custom email authentication backend:
  - `authentication/backends.py`
- Custom middleware:
  - inactivity timeout
  - custom 403/404 handling
- Strong password validation in forms/validators.

### Event Hooks
- Signals in `authentication/signals.py`:
  - auto-create foodbank trial subscription
  - admin login/logout tracking

---

## 5) Core Domain Model (Key Entities)

From `authentication/models.py`:
- `CustomUser` + profile models:
  - `DonorProfile`
  - `FoodBankProfile`
  - `RecipientProfile`
- Request models:
  - `RecipientRequest`
  - `FoodBankRequest`
  - `RequestManagement`
- Donation models:
  - `Donation`
  - `DonationAllocation`
  - `UnspecifiedDonationManagement`
  - `DonationResponse`
  - `DonationDiscussion` and `DonationDiscussionMessage`
- Platform ops:
  - `Notification`
  - `FoodBankSubscription`
  - `SubscriptionPayment`
  - `SystemSupportDonation`
  - `AccountDeletionRequest`
  - `AdminLoginLog`
  - `AdminCode`
  - `NewsSection`

---

## 6) Project Size and Complexity Signals

Approximate source size (excluding env/media/staticfiles):
- Python: `~59,823` lines
- HTML templates: `~103,620` lines
- CSS: `~2,444` lines
- JS: `~494` lines

### Module/File Counts (Current Repository Snapshot)

- Django apps: `3` (`authentication`, `custom_admin`, `reports`)
- Python files total: `185`
- Python modules (excluding migrations): `79`
  - `authentication`: `35` modules (`~38,050` lines)
  - `custom_admin`: `22` modules (`~14,756` lines)
  - `reports`: `11` modules (`~3,486` lines)
  - `FoodBankHub` (project package): `9` modules (`~619` lines)
  - root-level Python files: `2` (`~77` lines)
- Migration modules:
  - `authentication` migrations: `105` files (`~2,835` lines)
- HTML templates total: `263`
  - `templates/`: `157` files (`~67,307` lines)
  - `custom_admin/templates/`: `87` files (`~27,395` lines)
  - `reports/templates/`: `18` files (`~7,772` lines)
- Static frontend files:
  - JavaScript: `4` files (`~494` lines)
  - CSS: `4` files (`~2,444` lines)

Major hotspots:
- `authentication/views.py` (~24,775 lines)
- `custom_admin/views.py` (~5,291 lines)
- `custom_admin/views_donations.py` (~5,289 lines)
- `authentication/donation_views.py` (~3,274 lines)

Implication: business logic is very feature-rich and concentrated in a few large modules.

---

## 7) What You Should Learn for This Project

## A. Django Fundamentals (must-have)
- Django request/response lifecycle
- URL routing and named URLs
- Django ORM queries and relationships
- ModelForm patterns and validation
- Template inheritance and template tags
- Migrations and schema evolution

### General Django Knowledge You Should Have (Baseline)
- Project vs app structure (`settings.py`, `urls.py`, `apps.py`)
- Authentication/authorization (custom user model, login decorators, permissions)
- Middleware flow (request -> middleware -> view -> response)
- Class-based vs function-based views
- Query optimization basics (`select_related`, `prefetch_related`, avoiding N+1)
- Form lifecycle (`__init__`, `clean_<field>`, `clean`, `save`)
- Static/media handling and file uploads
- Django signals and when to avoid overusing them
- Writing tests with Django `TestCase` and client
- Deployment basics (DEBUG, ALLOWED_HOSTS, secrets, DB switching)

## B. Project-Specific Patterns
- Custom user model and role-based flows
- Donation lifecycle and status transitions
- Request lifecycle (recipient -> foodbank -> donor -> allocation)
- Stock/quantity/amount handling rules
- Notes/decline/acceptance audit data across roles

## C. Data & Database Skills
- Designing/optimizing relational queries
- Understanding join-heavy list pages
- PostgreSQL migration and verification strategy
- Data consistency checks for allocations and partial fulfillment

## D. Payments and Integrations
- Stripe PaymentIntent + webhook flow
- M-Pesa STK push callback handling
- Secure env configuration and webhook safety

## E. Reporting & Exports
- ReportLab PDF table layout patterns
- openpyxl sheet generation and formatting
- Keeping table UI and exports logically consistent

## F. Frontend Maintenance Skills
- Bootstrap table and modal patterns
- Responsive table tuning without horizontal scroll
- JS for inline row actions, preview tables, and state persistence

## G. Quality and Maintainability
- Writing focused tests for critical flows
- Isolating logic from very large view files
- Reusable helper/service extraction
- Regression-safe refactoring strategy

---

## 8) Suggested Learning Path (Practical)

### Phase 1: Orientation (1-2 days)
- Read:
  - `FoodBankHub/settings.py`
  - `FoodBankHub/urls.py`
  - `authentication/urls.py`
  - `authentication/models.py`

### Phase 2: Core User Flows (2-4 days)
- Trace end-to-end:
  - donor creates donation
  - foodbank accepts/declines
  - recipient accepts/declines/acknowledges
- Focus files:
  - `authentication/views.py`
  - `authentication/donation_views.py`
  - related templates in `templates/authentication`, `templates/foodbank`, `templates/recipient`

### Phase 3: Filters, Tables, and Exports (2-3 days)
- Understand parity between:
  - on-screen table columns
  - CSV/Excel/PDF exports
- Focus files:
  - `authentication/donor_export_views.py`
  - `authentication/available_donations_exports.py`
  - `reports/*`

### Phase 4: Payments + Subscriptions (1-2 days)
- Stripe views/webhook in `authentication/views.py`
- M-Pesa service in `authentication/mpesa_utils.py`
- Subscription lifecycle in `authentication/models.py` + `authentication/subscription_views.py`

### Phase 5: Admin Operations (2-3 days)
- `custom_admin/urls.py`
- `custom_admin/views.py`
- `custom_admin/views_donations.py`
- `custom_admin/views_impact.py`

---

## 9) Recommended Next Technical Improvements

- Split large view modules into feature services.
- Add stronger automated test coverage for:
  - payment callbacks
  - allocation math (quantity/amount)
  - status transitions and filtering
- Formalize PostgreSQL as primary production target.
- Add CI for tests/lint/migrations.
- Introduce API boundaries for table-heavy pages (optional, phased).

---

## 10) Quick Reference: Key Files

- Settings: `FoodBankHub/settings.py`
- Root routes: `FoodBankHub/urls.py`
- Core routes: `authentication/urls.py`
- Core models: `authentication/models.py`
- Core business views: `authentication/views.py`
- Donation-focused views: `authentication/donation_views.py`
- Donor detail/export views:
  - `authentication/donor_detailed_views.py`
  - `authentication/donor_export_views.py`
- Reports app:
  - `reports/urls.py`
  - `reports/views.py`
  - `reports/foodbank_reports.py`
- Custom admin:
  - `custom_admin/urls.py`
  - `custom_admin/views.py`
  - `custom_admin/views_donations.py`
