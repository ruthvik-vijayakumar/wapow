"""
Merge sports, style, technology, travel, wellbeing collections into a single 'articles' collection.
Adds a 'category' field to each document (sports, style, technology, travel, wellbeing).

Run: poetry run python -m api.scripts.merge_articles_collections

Options:
  --dry-run     Print what would be done without writing to DB
  --clear-target  Clear 'articles' before merge (use if re-running)
  --drop-old    Drop the old collections after merge (default: keep them)
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from api.db import get_client
from api.config import MONGODB_DB_NAME

SOURCE_COLLECTIONS = ["sports", "style", "technology", "travel", "wellbeing"]
TARGET_COLLECTION = "articles"


def run(dry_run: bool = False, drop_old: bool = False, clear_target: bool = False):
    client = get_client()
    db = client[MONGODB_DB_NAME]
    target = db[TARGET_COLLECTION]

    if clear_target and not dry_run:
        target.delete_many({})
        print(f"Cleared {TARGET_COLLECTION}")
    elif clear_target and dry_run:
        print(f"Would clear {TARGET_COLLECTION}")

    total_inserted = 0

    for coll_name in SOURCE_COLLECTIONS:
        coll = db[coll_name]
        count = coll.count_documents({})
        print(f"  {coll_name}: {count} documents")

        if count == 0:
            continue

        cursor = coll.find({})
        docs = list(cursor)

        for doc in docs:
            # Add category field (avoid overwriting if already present)
            doc["category"] = coll_name
            # Remove MongoDB _id so we get a fresh insert, or keep it for dedup
            # Keeping _id: documents from different collections could have same _id format
            # ObjectIds are unique per doc, so we keep them

        if not dry_run:
            if docs:
                result = target.insert_many(docs, ordered=False)
                total_inserted += len(result.inserted_ids)
                print(f"    -> Inserted {len(result.inserted_ids)} into {TARGET_COLLECTION}")
        else:
            total_inserted += len(docs)
            print(f"    -> Would insert {len(docs)} into {TARGET_COLLECTION}")

    print(f"\nTotal inserted: {total_inserted}")

    if not dry_run and drop_old and total_inserted > 0:
        for coll_name in SOURCE_COLLECTIONS:
            db[coll_name].drop()
            print(f"Dropped collection: {coll_name}")

    # Create index on category for efficient filtering
    if not dry_run and total_inserted > 0:
        target.create_index("category")
        print(f"Created index on 'category' in {TARGET_COLLECTION}")


def main():
    parser = argparse.ArgumentParser(description="Merge article collections into single 'articles' collection")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--clear-target", action="store_true", help="Clear articles collection before merge")
    parser.add_argument("--drop-old", action="store_true", help="Drop source collections after merge")
    args = parser.parse_args()

    print("Merge article collections -> articles (with category field)")
    print("Source collections:", SOURCE_COLLECTIONS)
    if args.dry_run:
        print("DRY RUN - no changes will be made")
    run(dry_run=args.dry_run, drop_old=args.drop_old, clear_target=args.clear_target)


if __name__ == "__main__":
    main()
