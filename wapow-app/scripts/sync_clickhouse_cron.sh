#!/usr/bin/env bash
set -euo pipefail

# Simple wrapper for running the ClickHouse → Neo4j sync script from cron.
# Example crontab (run every 15 minutes):
# */15 * * * * cd /opt/wapow/wapow-app && /usr/bin/env bash scripts/sync_clickhouse_cron.sh >> /var/log/wapow-sync.log 2>&1

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Activate virtualenv if you use one; for Docker, you typically run this
# inside the app container with the correct environment already set.

python -m api.scripts.sync_clickhouse_to_neo4j

