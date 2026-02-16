#!/bin/bash
set -e

clickhouse client -n <<'SQL'

CREATE DATABASE IF NOT EXISTS wapow_analytics;

CREATE TABLE IF NOT EXISTS wapow_analytics.events (
    event_id      UUID DEFAULT generateUUIDv4(),
    event_type    LowCardinality(String),
    user_id       String DEFAULT '',
    session_id    String,
    content_id    String DEFAULT '',
    content_type  LowCardinality(String) DEFAULT '',
    category      LowCardinality(String) DEFAULT '',
    timestamp     DateTime64(3) DEFAULT now64(3),
    properties    String DEFAULT '{}',
    ip            String DEFAULT '',
    user_agent    String DEFAULT '',
    device_type   LowCardinality(String) DEFAULT '',
    country       LowCardinality(String) DEFAULT '',
    city          String DEFAULT '',
    referrer      String DEFAULT ''
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_type, user_id, timestamp)
TTL toDateTime(timestamp) + INTERVAL 1 YEAR;

CREATE TABLE IF NOT EXISTS wapow_analytics.content_engagement_hourly (
    content_id    String,
    content_type  LowCardinality(String),
    category      LowCardinality(String),
    hour          DateTime,
    views         UInt64,
    likes         UInt64,
    saves         UInt64,
    shares        UInt64,
    comments      UInt64,
    total_dwell_ms UInt64,
    event_count   UInt64
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (content_id, hour);

CREATE MATERIALIZED VIEW IF NOT EXISTS wapow_analytics.mv_content_engagement_hourly
TO wapow_analytics.content_engagement_hourly
AS SELECT
    content_id,
    content_type,
    category,
    toStartOfHour(timestamp) AS hour,
    countIf(event_type = 'view')    AS views,
    countIf(event_type = 'like')    AS likes,
    countIf(event_type = 'save')    AS saves,
    countIf(event_type = 'share')   AS shares,
    countIf(event_type = 'comment') AS comments,
    sumIf(
        toUInt64OrZero(JSONExtractString(properties, 'dwell_time_ms')),
        event_type = 'dwell'
    ) AS total_dwell_ms,
    count() AS event_count
FROM wapow_analytics.events
WHERE content_id != ''
GROUP BY content_id, content_type, category, hour;

CREATE TABLE IF NOT EXISTS wapow_analytics.user_activity_daily (
    user_id       String,
    day           Date,
    views         UInt64,
    likes         UInt64,
    saves         UInt64,
    shares        UInt64,
    comments      UInt64,
    total_dwell_ms UInt64,
    sessions      UInt64,
    event_count   UInt64
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (user_id, day);

CREATE MATERIALIZED VIEW IF NOT EXISTS wapow_analytics.mv_user_activity_daily
TO wapow_analytics.user_activity_daily
AS SELECT
    user_id,
    toDate(timestamp) AS day,
    countIf(event_type = 'view')    AS views,
    countIf(event_type = 'like')    AS likes,
    countIf(event_type = 'save')    AS saves,
    countIf(event_type = 'share')   AS shares,
    countIf(event_type = 'comment') AS comments,
    sumIf(
        toUInt64OrZero(JSONExtractString(properties, 'dwell_time_ms')),
        event_type = 'dwell'
    ) AS total_dwell_ms,
    uniq(session_id) AS sessions,
    count() AS event_count
FROM wapow_analytics.events
WHERE user_id != ''
GROUP BY user_id, day;

SQL

echo "ClickHouse schema initialized successfully"
