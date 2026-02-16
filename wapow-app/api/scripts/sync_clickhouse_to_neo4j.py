#!/usr/bin/env python3
"""Sync ClickHouse interaction data into Neo4j to enrich the recommendation engine.

Reads aggregated user-content interactions from ClickHouse and creates/updates
Neo4j graph relationships:

  - (User)-[:READ {engagement_score}]->(Article)
  - (User)-[:INTERESTED_IN {weight}]->(Category)
  - (User)-[:READS_AT {frequency}]->(Hour)

Run periodically (e.g. every 15 minutes via cron) or manually:

    python -m api.scripts.sync_clickhouse_to_neo4j

Environment variables:
    CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_DB  — ClickHouse connection
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD            — Neo4j connection
"""

from __future__ import annotations

import logging
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path so api.config imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import clickhouse_connect
from neo4j import GraphDatabase

from api.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("sync_ch_neo4j")

# ── ClickHouse connection ─────────────────────────────────────────────────────

CH_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_DB = os.getenv("CLICKHOUSE_DB", "wapow_analytics")


def get_ch_client():
    return clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, database=CH_DB)


# ── Neo4j connection ──────────────────────────────────────────────────────────

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# ── Sync: user READ relationships ─────────────────────────────────────────────

def sync_read_relationships(ch, neo4j_driver, since_hours: int = 24):
    """Create/update (User)-[:READ]->(Article) relationships from views + dwell."""
    logger.info("Syncing READ relationships (last %d hours)...", since_hours)

    rows = ch.query(
        """
        SELECT
            user_id,
            content_id,
            content_type,
            category,
            countIf(event_type = 'view') AS views,
            sumIf(
                toUInt64OrZero(JSONExtractString(properties, 'dwell_time_ms')),
                event_type = 'dwell'
            ) AS total_dwell_ms,
            countIf(event_type = 'like') AS likes,
            countIf(event_type = 'save') AS saves,
            countIf(event_type = 'share') AS shares
        FROM events
        WHERE user_id != ''
          AND content_id != ''
          AND timestamp >= now() - INTERVAL {since:UInt32} HOUR
        GROUP BY user_id, content_id, content_type, category
        """,
        parameters={"since": since_hours},
    )

    count = 0
    with neo4j_driver.session() as session:
        for row in rows.result_rows:
            user_id, content_id, content_type, category, views, dwell_ms, likes, saves, shares = row

            # Compute an engagement score (0-1 range)
            # dwell weight: log(dwell_ms / 1000) capped at 5 min
            dwell_score = min(math.log1p(dwell_ms / 1000) / math.log1p(300), 1.0)
            interaction_score = min((likes * 0.3 + saves * 0.4 + shares * 0.3) / 1.0, 1.0)
            view_score = min(views / 3.0, 1.0)
            engagement = round(dwell_score * 0.5 + interaction_score * 0.3 + view_score * 0.2, 4)

            session.run(
                """
                MERGE (u:User {id: $user_id})
                MERGE (a:Article {id: $content_id})
                ON CREATE SET a.content_type = $content_type, a.category = $category
                MERGE (u)-[r:READ]->(a)
                SET r.engagement_score = $engagement,
                    r.views = $views,
                    r.total_dwell_ms = $dwell_ms,
                    r.likes = $likes,
                    r.saves = $saves,
                    r.shares = $shares,
                    r.updated_at = datetime()
                """,
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                category=category,
                engagement=engagement,
                views=views,
                dwell_ms=int(dwell_ms),
                likes=likes,
                saves=saves,
                shares=shares,
            )
            count += 1

    logger.info("Synced %d READ relationships", count)


# ── Sync: user INTERESTED_IN relationships ────────────────────────────────────

def sync_category_interests(ch, neo4j_driver, since_hours: int = 168):
    """Update (User)-[:INTERESTED_IN]->(Category) weights from real engagement."""
    logger.info("Syncing INTERESTED_IN relationships (last %d hours)...", since_hours)

    rows = ch.query(
        """
        SELECT
            user_id,
            category,
            count()                      AS event_count,
            uniq(content_id)             AS unique_content,
            sumIf(
                toUInt64OrZero(JSONExtractString(properties, 'dwell_time_ms')),
                event_type = 'dwell'
            ) AS total_dwell_ms
        FROM events
        WHERE user_id != ''
          AND category != ''
          AND timestamp >= now() - INTERVAL {since:UInt32} HOUR
        GROUP BY user_id, category
        """,
        parameters={"since": since_hours},
    )

    count = 0
    with neo4j_driver.session() as session:
        for row in rows.result_rows:
            user_id, category, event_count, unique_content, dwell_ms = row

            # Weight: combination of breadth (unique content) and depth (dwell)
            breadth = min(unique_content / 10.0, 1.0)
            depth = min(math.log1p(dwell_ms / 1000) / math.log1p(600), 1.0)
            weight = round(breadth * 0.4 + depth * 0.6, 4)

            session.run(
                """
                MERGE (u:User {id: $user_id})
                MERGE (c:Category {name: $category})
                MERGE (u)-[r:INTERESTED_IN]->(c)
                SET r.weight = $weight,
                    r.event_count = $event_count,
                    r.unique_content = $unique_content,
                    r.total_dwell_ms = $dwell_ms,
                    r.updated_at = datetime()
                """,
                user_id=user_id,
                category=category,
                weight=weight,
                event_count=event_count,
                unique_content=unique_content,
                dwell_ms=int(dwell_ms),
            )
            count += 1

    logger.info("Synced %d INTERESTED_IN relationships", count)


# ── Sync: user READS_AT time patterns ─────────────────────────────────────────

def sync_reading_times(ch, neo4j_driver, since_hours: int = 168):
    """Update (User)-[:READS_AT]->(Hour) patterns from real timestamps."""
    logger.info("Syncing READS_AT relationships (last %d hours)...", since_hours)

    rows = ch.query(
        """
        SELECT
            user_id,
            toHour(timestamp) AS hour,
            count() AS frequency
        FROM events
        WHERE user_id != ''
          AND event_type IN ('view', 'dwell')
          AND timestamp >= now() - INTERVAL {since:UInt32} HOUR
        GROUP BY user_id, hour
        """,
        parameters={"since": since_hours},
    )

    count = 0
    with neo4j_driver.session() as session:
        for row in rows.result_rows:
            user_id, hour, frequency = row

            session.run(
                """
                MERGE (u:User {id: $user_id})
                MERGE (h:Hour {hour: $hour})
                MERGE (u)-[r:READS_AT]->(h)
                SET r.frequency = $frequency,
                    r.updated_at = datetime()
                """,
                user_id=user_id,
                hour=int(hour),
                frequency=int(frequency),
            )
            count += 1

    logger.info("Synced %d READS_AT relationships", count)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    logger.info("Starting ClickHouse → Neo4j sync...")

    ch = get_ch_client()
    neo4j_driver = get_neo4j_driver()

    try:
        sync_read_relationships(ch, neo4j_driver, since_hours=24)
        sync_category_interests(ch, neo4j_driver, since_hours=168)
        sync_reading_times(ch, neo4j_driver, since_hours=168)
        logger.info("Sync complete.")
    finally:
        ch.close()
        neo4j_driver.close()


if __name__ == "__main__":
    main()
