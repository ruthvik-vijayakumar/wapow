"""Configuration for the event collector service."""

import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "3002"))

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "wapow_analytics")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

print(f"CLICKHOUSE_HOST: {CLICKHOUSE_HOST}")
print(f"CLICKHOUSE_PORT: {CLICKHOUSE_PORT}")
print(f"CLICKHOUSE_DB: {CLICKHOUSE_DB}")
print(f"CLICKHOUSE_USER: {CLICKHOUSE_USER}")
print(f"CLICKHOUSE_PASSWORD: {CLICKHOUSE_PASSWORD}")



# Optional MaxMind GeoLite2 database path
MAXMIND_DB_PATH = os.getenv("MAXMIND_DB_PATH", "")

# CORS — allow all origins in dev; restrict in production
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Writer buffer settings
FLUSH_INTERVAL_SECONDS = float(os.getenv("FLUSH_INTERVAL_SECONDS", "1.0"))
FLUSH_BATCH_SIZE = int(os.getenv("FLUSH_BATCH_SIZE", "500"))
