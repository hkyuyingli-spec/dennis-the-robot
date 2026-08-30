import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import initialization function from analyze_firebase
try:
    from analyze_firebase import init_firebase
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def parse_timestamp(ts_val):
    """Converts Firestore Timestamp or ISO string into a timezone-aware UTC datetime."""
    if ts_val is None:
        return None
    # If it's a Firestore Timestamp object (has to_datetime or python datetime interface)
    if hasattr(ts_val, 'to_datetime'):
        dt = ts_val.to_datetime()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val
    if isinstance(ts_val, str):
        # Clean trailing 'Z' if present
        clean_str = ts_val.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None

def format_time_ago(delta):
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        return "in the future"
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    return ", ".join(parts) + " ago"

def run_recency_and_user_analysis():
    print("=== FIREBASE FIRESTORE RECENCY & UNIQUE USER ANALYSIS ===")
    print("Connecting to Firestore...")
    
    try:
        db = init_firebase()
        print(" Successfully connected to Firestore.\n")
    except Exception as e:
        print(f" Failed to connect to Firestore: {e}")
        sys.exit(1)

    now_utc = datetime.now(timezone.utc)
    print(f"Current System Time (UTC): {now_utc.isoformat()}\n")

    collections_config = [
        {"name": "nutribot_logs", "fields": ["question", "category"]},
        {"name": "nutribot_metrics", "fields": ["event_type", "goal", "age", "gender"]}
    ]

    all_logs_sessions = set()
    all_metrics_sessions = set()
    overall_most_recent_dt = None
    overall_most_recent_collection = None

    for config in collections_config:
        col_name = config["name"]
        print(f"==================================================")
        print(f"📊 Collection: '{col_name}'")
        print(f"==================================================")
        
        docs_ref = db.collection(col_name).stream()
        records = []

        for doc in docs_ref:
            d = doc.to_dict()
            d['id'] = doc.id
            ts = parse_timestamp(d.get('timestamp'))
            d['parsed_timestamp'] = ts
            session_id = d.get('session_id')
            if session_id:
                if col_name == "nutribot_logs":
                    all_logs_sessions.add(session_id)
                elif col_name == "nutribot_metrics":
                    all_metrics_sessions.add(session_id)
            records.append(d)

        total_docs = len(records)
        print(f"Total Documents: {total_docs}")

        # Filter out documents without valid parsed timestamp for recency sorting
        valid_records = [r for r in records if r['parsed_timestamp'] is not None]
        valid_records.sort(key=lambda x: x['parsed_timestamp'], reverse=True)

        if valid_records:
            most_recent = valid_records[0]
            most_recent_dt = most_recent['parsed_timestamp']
            time_diff = now_utc - most_recent_dt
            time_ago_str = format_time_ago(time_diff)
            is_stale = time_diff.total_seconds() > (48 * 3600)

            if overall_most_recent_dt is None or most_recent_dt > overall_most_recent_dt:
                overall_most_recent_dt = most_recent_dt
                overall_most_recent_collection = col_name

            print(f"Most Recent Entry Timestamp: {most_recent_dt.isoformat()}")
            print(f"Time Since Most Recent Entry: {time_ago_str}")
            if is_stale:
                print("⚠️ **WARNING: Most recent entry is MORE than 48 hours old!**")
            else:
                print("✅ **Status: Active (within last 48 hours)**")

            print(f"\n--- Top 5 Most Recent Entries ---")
            for i, rec in enumerate(valid_records[:5], 1):
                extra_fields = {k: rec.get(k) for k in config["fields"] if k in rec}
                print(f"{i}. Timestamp: {rec['parsed_timestamp'].isoformat()}")
                print(f"   Session ID: {rec.get('session_id', 'N/A')}")
                for k, v in extra_fields.items():
                    print(f"   {k}: {v}")
                print()
        else:
            print("No valid timestamps found in this collection.\n")

    combined_sessions = all_logs_sessions.union(all_metrics_sessions)

    print("==================================================")
    print("👤 UNIQUE USER (SESSION_ID) SUMMARY")
    print("==================================================")
    print(f"• Unique session_ids in 'nutribot_logs':    {len(all_logs_sessions)}")
    print(f"• Unique session_ids in 'nutribot_metrics': {len(all_metrics_sessions)}")
    print(f"• Combined DISTINCT session_ids:            {len(combined_sessions)}")
    print("==================================================")

    if overall_most_recent_dt:
        overall_diff = now_utc - overall_most_recent_dt
        overall_ago_str = format_time_ago(overall_diff)
        overall_stale = overall_diff.total_seconds() > (48 * 3600)
        print("\n=== OVERALL DATABASE RECENCY SUMMARY ===")
        print(f"Single Most Recent Entry Across All Collections:")
        print(f"  Collection: {overall_most_recent_collection}")
        print(f"  Timestamp:  {overall_most_recent_dt.isoformat()}")
        print(f"  Elapsed:    {overall_ago_str}")
        if overall_stale:
            print("\n⚠️ **FLAG: The most recent database entry is MORE THAN 48 HOURS OLD!**")
        else:
            print("\n✅ **FLAG: The database has recent entries within the last 48 hours.**")

if __name__ == "__main__":
    run_recency_and_user_analysis()
