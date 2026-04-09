# Production image for Render (WeasyPrint needs system libraries).
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libjpeg62-turbo \
    libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# So Django file logging never fails if DEBUG is ever True without mkdir
RUN mkdir -p /app/logs

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Build-time collectstatic (no real DB or secrets required)
RUN SECRET_KEY=build-only-not-for-production \
    DEBUG=False \
    ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

EXPOSE 10000

CMD exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 120
