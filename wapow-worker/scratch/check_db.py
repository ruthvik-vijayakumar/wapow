import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add scraper path to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.db.mongodb import get_collection

try:
    coll_runs = get_collection("scraper_runs")
    raw_runs = list(coll_runs.find())
    print(f"Loaded {len(raw_runs)} raw runs.")
    
    runs = []
    for run in raw_runs:
        run["_id"] = str(run["_id"])
        if "start_time" in run and isinstance(run["start_time"], datetime):
            run["start_time"] = run["start_time"].isoformat()
        if "end_time" in run and isinstance(run["end_time"], datetime):
            run["end_time"] = run["end_time"].isoformat()
        if "saved_articles" in run:
            run.pop("saved_articles", None)
        runs.append(run)
        
    # Attempt to dump to JSON
    json_str = json.dumps(runs)
    print("Serialization test: SUCCESS")
except Exception as e:
    print(f"Serialization test: FAILED - {e}")
