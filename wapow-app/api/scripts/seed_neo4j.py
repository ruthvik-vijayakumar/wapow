"""
Seed Neo4j with minimal graph data so recommendation endpoints return results.

Creates: Locations, Hours, Categories, Articles, Users, and READ/INTERESTED_IN/
READS_AT/LIVES_IN/BELONGS_TO/PEAKS_AT/VIEWED_IN relationships.

Run from project root:
  poetry run python -m api.scripts.seed_neo4j
  # or
  PYTHONPATH=. python -m api.scripts.seed_neo4j
"""
import random
import sys
from pathlib import Path

# Ensure api is on path when run as script
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from neo4j import GraphDatabase
from api.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


def seed(driver):
    with driver.session() as session:
        # 1. Locations
        for name in ("DMV", "National", "International"):
            session.run(
                "MERGE (l:Location {name: $name}) SET l.id = $name",
                name=name,
            )
        print("Created Location nodes: DMV, National, International")

        # 2. Hours 0-23
        for hour in range(24):
            period = "Morning" if 6 <= hour < 12 else "Afternoon" if 12 <= hour < 18 else "Evening" if 18 <= hour < 24 else "Night"
            display = f"{12 if hour == 0 else hour if hour <= 12 else hour - 12}:00 {'AM' if hour < 12 else 'PM'}"
            session.run(
                "MERGE (h:Hour {hour: $hour}) SET h.display_time = $display, h.period = $period",
                hour=hour,
                display=display,
                period=period,
            )
        print("Created Hour nodes 0-23")

        # 3. Categories (match recommendation query: sports, technology, lifestyle, travel, food, business)
        categories = ["sports", "style", "technology", "travel", "wellbeing", "lifestyle", "food", "business"]
        for name in categories:
            session.run("MERGE (c:Category {name: $name})", name=name)
        print("Created Category nodes:", ", ".join(categories))

        # 4. Sample articles with BELONGS_TO, PEAKS_AT, pageviews, engagement_score
        articles = []
        for i in range(1, 21):
            aid = f"art_{i}"
            cat = random.choice(categories)
            hour = random.randint(8, 22)
            session.run(
                """
                MERGE (a:Article {id: $id})
                SET a.pageviews = $pageviews, a.engagement_score = $engagement,
                    a.canonical_url = $url, a.word_count = $word_count
                """,
                id=aid,
                pageviews=random.randint(100, 5000),
                engagement=round(random.uniform(0.3, 0.9), 2),
                url=f"https://example.com/article/{aid}",
                word_count=random.randint(400, 2000),
            )
            session.run(
                "MATCH (a:Article {id: $aid}) MATCH (c:Category {name: $cat}) MERGE (a)-[:BELONGS_TO]->(c)",
                aid=aid,
                cat=cat,
            )
            session.run(
                "MATCH (a:Article {id: $aid}) MATCH (h:Hour {hour: $hour}) MERGE (a)-[:PEAKS_AT]->(h)",
                aid=aid,
                hour=hour,
            )
            loc = random.choice(["DMV", "National", "International"])
            session.run(
                "MATCH (a:Article {id: $aid}) MATCH (l:Location {name: $loc}) MERGE (a)-[:VIEWED_IN]->(l)",
                aid=aid,
                loc=loc,
            )
            articles.append({"id": aid, "category": cat, "hour": hour})
        print("Created 20 Article nodes with BELONGS_TO, PEAKS_AT, VIEWED_IN")

        # 5. Users: include id "1" and user_001..user_005 with INTERESTED_IN, LIVES_IN, READS_AT
        users_config = [
            {"id": "1", "name": "Alex", "location": "National", "categories": ["sports", "technology"], "hours": [9, 12, 18, 21]},
            {"id": "user_001", "name": "Zoe", "location": "DMV", "categories": ["technology", "lifestyle"], "hours": [10, 14, 20]},
            {"id": "user_002", "name": "Tyler", "location": "National", "categories": ["sports", "technology"], "hours": [9, 12, 19]},
            {"id": "user_003", "name": "Maya", "location": "International", "categories": ["travel", "wellbeing"], "hours": [11, 17, 21]},
            {"id": "user_004", "name": "Jordan", "location": "National", "categories": ["sports", "travel"], "hours": [7, 16, 22]},
            {"id": "user_005", "name": "Sam", "location": "DMV", "categories": ["sports", "style"], "hours": [8, 13, 20]},
        ]
        for u in users_config:
            session.run(
                """
                MERGE (u:User {id: $id})
                SET u.name = $name, u.location_preference = $location, u.reading_behavior = 'seed'
                """,
                id=u["id"],
                name=u["name"],
                location=u["location"],
            )
            session.run(
                "MATCH (u:User {id: $uid}) MATCH (l:Location {name: $loc}) MERGE (u)-[:LIVES_IN]->(l)",
                uid=u["id"],
                loc=u["location"],
            )
            for i, cat in enumerate(u["categories"]):
                session.run(
                    "MATCH (u:User {id: $uid}) MATCH (c:Category {name: $cat}) MERGE (u)-[r:INTERESTED_IN]->(c) SET r.interest_weight = $w",
                    uid=u["id"],
                    cat=cat,
                    w=1.0 - i * 0.2,
                )
            for h in u["hours"]:
                session.run(
                    "MATCH (u:User {id: $uid}) MATCH (h:Hour {hour: $hour}) MERGE (u)-[r:READS_AT]->(h) SET r.frequency = 0.8",
                    uid=u["id"],
                    hour=h,
                )
        print("Created User nodes (including id '1') with LIVES_IN, INTERESTED_IN, READS_AT")

        # 6. READ relationships: each user reads some articles (so similar users can recommend)
        for u in users_config:
            uid = u["id"]
            candidates = [a for a in articles if a["category"] in u["categories"]] + [
                a for a in articles if a["category"] not in u["categories"]
            ][:5]
            read_ids = list({a["id"] for a in candidates})[:12]
            for i, aid in enumerate(read_ids):
                session.run(
                    """
                    MATCH (u:User {id: $uid}) MATCH (a:Article {id: $aid})
                    MERGE (u)-[r:READ]->(a)
                    SET r.engagement_score = $eng, r.reading_time_seconds = $sec
                    """,
                    uid=uid,
                    aid=aid,
                    eng=round(0.3 + 0.1 * (12 - i) + random.uniform(-0.1, 0.1), 2),
                    sec=random.randint(180, 1200),
                )
            print(f"  User {uid}: {len(read_ids)} READ relationships")
        print("Created READ relationships (user -> article)")
        print("\nDone. Try: POST /api/recommendations with body {\"user_id\": \"1\", \"category\": \"sports\"}")


if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        seed(driver)
    finally:
        driver.close()