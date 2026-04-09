<!-- GitHub Copilot / AI agent instructions for FoodBankHub -->
# FoodBankHub — Copilot Instructions

Purpose: help AI coding agents become productive quickly in this repository.

- **Big picture:** a Django monolith (Django 5.2.x) with three primary apps:
  - `authentication` — core business logic: custom user model, donations, requests, payments, notifications (very large `views.py` and `models.py`).
  - `custom_admin` — custom admin dashboard and workflows (approval, support, analytics).
  - `reports` — PDF/Excel reporting helpers and endpoints.

- **Entry points & settings:** `FoodBankHub/settings.py` contains the canonical configuration (SQLite for local, PostgreSQL commented for production). Key settings: `AUTH_USER_MODEL = 'authentication.CustomUser'`, `AUTHENTICATION_BACKENDS` uses `authentication.backends.EmailBackend`, Stripe and email keys are read via `python-decouple`.

- **Auth & roles:** `authentication.models.CustomUser` is email-based (USERNAME_FIELD = 'email') and has `user_type` choices: `ADMIN`, `DONOR`, `FOODBANK`, `RECIPIENT`. Food bank approval is stored on `FoodBankProfile.is_approved`.

- **Patterns & conventions to follow:**
  - Use email-based auth; note `authentication/backends.py` provides `EmailBackend`. Some legacy calls use `authenticate(..., username=...)` — code accepts either pattern in practice.
  - Large views are centralized in `authentication/views.py`; when adding related functionality prefer creating or reusing scoped modules (`donation_views.py`, `subscription_views.py`, etc.) rather than further bloating the main file.
  - Use `select_related`/`prefetch_related` as already used in list views to avoid N+1 queries.
  - Pagination uses Django's `Paginator` consistently in admin and public lists.
  - Templates live under `templates/` with app subfolders (e.g. `templates/authentication/`, `templates/custom_admin/`). Static files under `static/` and media uploads under `media/`.

- **Important files to inspect when changing behavior:**
  - `authentication/models.py`, `authentication/views.py`, `authentication/forms.py`, `authentication/utils.py`, `authentication/middleware.py`, `authentication/backends.py`.
  - `custom_admin/views.py`, `custom_admin/config.py`, `custom_admin/decorators.py`.
  - `FoodBankHub/settings.py` for feature flags, keys, session/CSRF configuration.

- **Integrations & side-effects:**
  - Payments: Stripe (`stripe` lib) and M-Pesa (`authentication/mpesa_utils.py`). Webhook endpoints: `authentication/urls.py` -> `stripe-webhook/` and `mpesa/callback/`.
  - Email: Gmail SMTP configured in `settings.py` using `python-decouple` env vars.
  - Reporting: PDF via `reportlab`, Excel via `openpyxl`/`xlsxwriter` (see `authentication/views.py` and `custom_admin/views.py`).

- **Local developer workflows (discoverable from repo):**
  - Create and activate a virtualenv (repo includes `env/` but local env recommended).
  - Install deps: `pip install -r requirements.txt`.
  - Run migrations: `python manage.py migrate`.
  - Create a superuser (CustomUser uses email): `python manage.py createsuperuser` (you will be prompted for `email`).
  - Run dev server: `python manage.py runserver`.
  - Collect static for production: `python manage.py collectstatic --noinput`.

  Example PowerShell commands:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py runserver
  ```

- **Debugging tips unique to this project:**
  - CSRF issues: there is a debug endpoint at `/csrf-debug/` and a custom failure view at `authentication/csrf_views.py`.
  - Logs: application logging writes to `logs/django.log` per `settings.py`.
  - Stripe/M-Pesa flows: use the webhook endpoints and `STRIPE_WEBHOOK_SECRET`/M-Pesa sandbox when testing.

- **Repository/CI notes:**
  - No repository-level Copilot/AGENT files found; this file should be the canonical AI-agent guide.
  - The project currently uses SQLite locally (`db.sqlite3`). Switch to PostgreSQL by editing `FoodBankHub/settings.py` and setting the environment vars noted in `PROJECT_ANALYSIS.md`.

- **When you modify code:**
  - Run migrations if models changed: `python manage.py makemigrations && python manage.py migrate`.
  - Verify critical paths manually: registration/login (foodbank approval flow), donation payment (Stripe/M-Pesa), and webhook endpoints.

If any part of this guide is unclear or you want more examples (e.g., common refactor patterns for breaking down `authentication/views.py`), tell me which areas to expand and I will iterate.
