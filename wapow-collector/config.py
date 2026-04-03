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

# CORS — comma-separated; * for dev; production: list Vercel + custom domain URLs
_cors_raw = os.getenv("CORS_ORIGINS", "*").strip()
if _cors_raw == "*":
    CORS_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
else:
    CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()] or ["*"]
    CORS_ALLOW_CREDENTIALS = CORS_ORIGINS != ["*"]

# Writer buffer settings
FLUSH_INTERVAL_SECONDS = float(os.getenv("FLUSH_INTERVAL_SECONDS", "1.0"))
FLUSH_BATCH_SIZE = int(os.getenv("FLUSH_BATCH_SIZE", "500"))
