"""Neo4j query class for recommendations (from grapow)."""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional

from api.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jQuery:
    """
    Neo4j query class focused on recommendations and data retrieval.
    """

    def __init__(
        self,
        uri: str = NEO4J_URI,
        user: str = NEO4J_USER,
        password: str = NEO4J_PASSWORD,
    ):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Neo4j: {e}") from e

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def find_similar_users_by_time(
        self,
        target_user_id: str,
        current_hour: int,
        time_window: int = 2,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        start_hour = (current_hour - time_window) % 24
        end_hour = (current_hour + time_window) % 24

        with self.driver.session() as session:
            if start_hour > end_hour:
                hour_filter = f"h.hour >= {start_hour} OR h.hour <= {end_hour}"
            else:
                hour_filter = f"h.hour >= {start_hour} AND h.hour <= {end_hour}"

            query = f"""
            MATCH (target:User {{id: $target_user_id}})
            MATCH (similar:User)-[:READS_AT]->(h:Hour)
            WHERE {hour_filter} AND similar.id <> $target_user_id
            OPTIONAL MATCH (target)-[:INTERESTED_IN]->(shared_cat:Category)<-[:INTERESTED_IN]-(similar)
            OPTIONAL MATCH (target)-[:LIVES_IN]->(shared_loc:Location)<-[:LIVES_IN]-(similar)
            OPTIONAL MATCH (target)-[:READS_AT]->(shared_hour:Hour)<-[:READS_AT]-(similar)
            WITH similar,
                count(DISTINCT shared_cat) as shared_categories,
                count(DISTINCT shared_loc) as shared_locations,
                count(DISTINCT shared_hour) as shared_hours,
                (count(DISTINCT shared_cat) * 0.4 +
                count(DISTINCT shared_loc) * 0.3 +
                count(DISTINCT shared_hour) * 0.3) as similarity_score
            WHERE similarity_score > 0
            MATCH (similar)-[r:READS_AT]->(h:Hour)
            WHERE {hour_filter}
            RETURN similar.id as user_id,
                similar.name as name,
                similar.age as age,
                similar.location_preference as location,
                similarity_score,
                collect({{hour: h.hour, frequency: r.frequency}}) as time_overlap
            ORDER BY similarity_score DESC
            LIMIT {limit}
            """
            result = session.run(query, target_user_id=target_user_id)
            return [
                {
                    "user_id": record["user_id"],
                    "name": record["name"],
                    "age": record["age"],
                    "location": record["location"],
                    "similarity_score": round(record["similarity_score"], 4),
                    "time_overlap": record["time_overlap"],
                }
                for record in result
            ]

    def get_collaborative_recommendations(
        self,
        target_user_id: str,
        current_hour: int,
        limit: int = 10,
        time_window: int = 2,
    ) -> Dict[str, Any]:
        similar_users = self.find_similar_users_by_time(
            target_user_id, current_hour, time_window, limit=5
        )
        if not similar_users:
            return {
                "recommendations": [],
                "similar_users": [],
                "method": "collaborative_filtering_time_based",
                "current_hour": current_hour,
                "time_window": f"±{time_window} hours",
                "message": "No similar users found for this time period",
            }

        similar_user_ids = [u["user_id"] for u in similar_users]
        with self.driver.session() as session:
            query = """
            MATCH (similar:User)-[r:READ]->(a:Article)
            WHERE similar.id IN $similar_user_ids
            AND NOT EXISTS {
                MATCH (target:User {id: $target_user_id})-[:READ]->(a)
            }
            WITH a,
                count(r) as read_by_similar_users,
                avg(r.engagement_score) as avg_user_engagement
            MATCH (a)-[:BELONGS_TO]->(c:Category)
            OPTIONAL MATCH (a)-[:PEAKS_AT]->(h:Hour)
            RETURN a.id as article_id,
                a.canonical_url as canonical_url,
                read_by_similar_users,
                round(avg_user_engagement, 3) as avg_user_engagement,
                a.engagement_score as article_engagement_score,
                round(
                    (read_by_similar_users * 0.25) +
                    (avg_user_engagement * 0.25) +
                    (a.engagement_score * 0.35) +
                    (log(a.pageviews + 1) / 10.0 * 0.15),
                    3
                ) as recommendation_score
            ORDER BY recommendation_score DESC, a.engagement_score DESC, a.pageviews DESC
            LIMIT $limit
            """
            result = session.run(
                query,
                similar_user_ids=similar_user_ids,
                target_user_id=target_user_id,
                limit=limit,
            )
            recommendations = [
                {"article_id": record["article_id"], "canonical_url": record["canonical_url"]}
                for record in result
            ]

        return {
            "recommendations": recommendations,
            "similar_users": similar_users,
            "method": "collaborative_filtering_time_based",
            "current_hour": current_hour,
            "time_window": f"±{time_window} hours",
            "total_recommendations": len(recommendations),
        }

    def find_similar_users_by_category(
        self,
        target_user_id: str,
        target_category: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            query = """
            MATCH (target:User {id: $target_user_id})
            MATCH (similar:User)-[sir:INTERESTED_IN]->(target_cat:Category {name: $target_category})
            WHERE similar.id <> $target_user_id
            OPTIONAL MATCH (target)-[:INTERESTED_IN]->(shared_cat:Category)<-[:INTERESTED_IN]-(similar)
            OPTIONAL MATCH (target)-[:LIVES_IN]->(shared_loc:Location)<-[:LIVES_IN]-(similar)
            OPTIONAL MATCH (target)-[:READS_AT]->(shared_hour:Hour)<-[:READS_AT]-(similar)
            WITH similar, sir.interest_weight as category_interest_weight,
                count(DISTINCT shared_cat) as shared_categories,
                count(DISTINCT shared_loc) as shared_locations,
                count(DISTINCT shared_hour) as shared_hours,
                (count(DISTINCT shared_cat) * 0.5 +
                count(DISTINCT shared_loc) * 0.25 +
                count(DISTINCT shared_hour) * 0.25 +
                sir.interest_weight * 0.3) as similarity_score
            WHERE similarity_score > 0
            MATCH (similar)-[ir:INTERESTED_IN]->(c:Category)
            RETURN similar.id as user_id,
                similar.name as name,
                similar.age as age,
                similar.location_preference as location,
                similarity_score,
                category_interest_weight,
                collect({category: c.name, weight: ir.interest_weight}) as all_interests,
                shared_categories,
                shared_locations,
                shared_hours
            ORDER BY similarity_score DESC
            LIMIT $limit
            """
            result = session.run(
                query,
                target_user_id=target_user_id,
                target_category=target_category,
                limit=limit,
            )
            return [
                {
                    "user_id": record["user_id"],
                    "name": record["name"],
                    "age": record["age"],
                    "location": record["location"],
                    "similarity_score": round(record["similarity_score"], 4),
                    "category_interest_weight": record["category_interest_weight"],
                    "all_interests": record["all_interests"],
                    "shared_patterns": {
                        "categories": record["shared_categories"],
                        "locations": record["shared_locations"],
                        "hours": record["shared_hours"],
                    },
                }
                for record in result
            ]

    def get_category_collaborative_recommendations(
        self,
        target_user_id: str,
        target_category: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        similar_users = self.find_similar_users_by_category(
            target_user_id, target_category, limit=7
        )
        if not similar_users:
            return {
                "recommendations": [],
                "similar_users": [],
                "method": "collaborative_filtering_category_based",
                "target_category": target_category,
                "message": f"No similar users found interested in '{target_category}'",
            }

        similar_user_ids = [u["user_id"] for u in similar_users]
        with self.driver.session() as session:
            query = """
            MATCH (similar:User)-[r:READ]->(a:Article)
            WHERE similar.id IN $similar_user_ids
            MATCH (a)-[:BELONGS_TO]->(c:Category)
            WHERE c.name = $target_category
            OR c.name IN ['technology', 'lifestyle', 'travel', 'sports', 'food', 'business']
            AND NOT EXISTS {
                MATCH (target:User {id: $target_user_id})-[:READ]->(a)
            }
            WITH a, c,
                count(r) as read_by_similar_users,
                avg(r.engagement_score) as avg_user_engagement,
                CASE WHEN c.name = $target_category THEN 1.5 ELSE 1.0 END as category_boost
            RETURN a.id as article_id,
                a.canonical_url as canonical_url,
                c.name as article_category,
                read_by_similar_users,
                round(avg_user_engagement, 3) as avg_user_engagement,
                a.engagement_score as article_engagement_score,
                category_boost,
                round(
                    (read_by_similar_users * 0.2) +
                    (avg_user_engagement * 0.25) +
                    (a.engagement_score * 0.4) +
                    (log(a.pageviews + 1) / 10.0 * 0.15) +
                    (category_boost * 0.1),
                    3
                ) as recommendation_score
            ORDER BY recommendation_score DESC, a.engagement_score DESC
            LIMIT $limit
            """
            result = session.run(
                query,
                similar_user_ids=similar_user_ids,
                target_user_id=target_user_id,
                target_category=target_category,
                limit=limit,
            )
            recommendations = [
                {"article_id": record["article_id"], "canonical_url": record["canonical_url"]}
                for record in result
            ]

        return {
            "recommendations": recommendations,
            "similar_users": similar_users,
            "method": "collaborative_filtering_category_based",
            "target_category": target_category,
            "total_recommendations": len(recommendations),
        }
