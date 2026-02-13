"""
Migrate saved_articles collection to users collection (embedded saved array).

Run: poetry run python -m api.scripts.migrate_saved_to_users

Options:
  --dry-run     Print what would be done without writing to DB
  --drop-old    Drop saved_articles collection after migration (default: keep it)
"""
import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from api.db import get_client
from api.config import MONGODB_DB_NAME, SAVED_ARTICLES_COLLECTION, USERS_COLLECTION


def run(dry_run: bool = False, drop_old: bool = False):
    client = get_client()
    db = client[MONGODB_DB_NAME]
    saved_coll = db[SAVED_ARTICLES_COLLECTION]
    users_coll = db[USERS_COLLECTION]

    count = saved_coll.count_documents({})
    print(f"saved_articles: {count} documents")

    if count == 0:
        print("Nothing to migrate.")
        return

    # Group by user_id
    grouped: dict[str, list[dict]] = defaultdict(list)
    for doc in saved_coll.find({}):
        user_id = doc.get("user_id")
        if not user_id:
            continue
        grouped[user_id].append({
            "article_id": str(doc.get("article_id", "")),
            "collection": doc.get("collection", "unknown"),
            "created_at": doc.get("created_at"),
        })

    print(f"Found {len(grouped)} users with saved content")

    total_upserted = 0
    for user_id, saved_list in grouped.items():
        # Sort by created_at desc (newest first) for consistency
        default_dt = datetime.min.replace(tzinfo=timezone.utc)
        saved_list.sort(key=lambda x: x.get("created_at") or default_dt, reverse=True)

        user_doc = {
            "user_id": user_id,
            "saved": saved_list,
        }

        if dry_run:
            print(f"  Would upsert user {user_id} with {len(saved_list)} saved items")
            total_upserted += 1
        else:
            users_coll.update_one(
                {"user_id": user_id},
                {"$set": {"saved": saved_list, "user_id": user_id}},
                upsert=True,
            )
            total_upserted += 1
            print(f"  Upserted user {user_id} with {len(saved_list)} saved items")

    print(f"\nTotal users migrated: {total_upserted}")

    if not dry_run and drop_old and total_upserted > 0:
        saved_coll.drop()
        print(f"Dropped collection: {SAVED_ARTICLES_COLLECTION}")

    if not dry_run and total_upserted > 0:
        users_coll.create_index("user_id", unique=True)
        print(f"Created unique index on 'user_id' in {USERS_COLLECTION}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate saved_articles to users collection (embedded saved array)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--drop-old", action="store_true", help="Drop saved_articles after migration")
    args = parser.parse_args()

    print("Migrate saved_articles -> users.saved")
    if args.dry_run:
        print("DRY RUN - no changes will be made")
    run(dry_run=args.dry_run, drop_old=args.drop_old)


if __name__ == "__main__":
    main()
