"""
Temporary settings file to export data from SQLite
"""
from .settings import *

# Override database to use SQLite for data export
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
