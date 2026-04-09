import sqlite3
import psycopg2
from decouple import config

# Connect to SQLite
sqlite_conn = sqlite3.connect('db.sqlite3')
sqlite_cursor = sqlite_conn.cursor()
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in sqlite_cursor.fetchall()]

sqlite_counts = {}
for table in tables:
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    sqlite_counts[table] = sqlite_cursor.fetchone()[0]

# Connect to Postgres
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection

postgres_counts = {}
with connection.cursor() as cursor:
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            postgres_counts[table] = cursor.fetchone()[0]
        except Exception as e:
            postgres_counts[table] = str(e)
            
print("TABLE COUNT COMPARISON:")
print(f"{'Table':<30} | {'SQLite Count':<12} | {'Postgres Count':<12}")
print("-" * 60)
for table in tables:
    sqlite_cnt = sqlite_counts[table]
    pg_cnt = postgres_counts.get(table, "N/A")
    if str(sqlite_cnt) != str(pg_cnt):
        print(f"{table:<30} | {sqlite_cnt:<12} | {str(pg_cnt):<12}")
    else:
        # For tables with equal counts, optionally hide or show them
        pass

print("\nMISMATCHED TABLES ONLY LISTED ABOVE.")

