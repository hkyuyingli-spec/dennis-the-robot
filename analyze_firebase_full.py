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
        clean_str = ts_val.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None

def format_span(delta):
    total_days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{total_days} days, {hours} hours, {minutes} minutes"

def run_full_diagnosis():
    print("=== FIREBASE FIRESTORE FULL DIAGNOSIS & DATE RANGE ANALYSIS ===\n")
    db = init_firebase()

    # ----------------------------------------------------
    # PART 3: USERS COLLECTION DIAGNOSIS
    # ----------------------------------------------------
    print("==================================================")
    print("3. USERS COLLECTION DIAGNOSIS")
    print("==================================================")

    users_docs = list(db.collection("users").stream())
    print(f"Direct 'users' collection total documents: {len(users_docs)}")
    for doc in users_docs:
        print(f"  - Document ID: '{doc.id}': {doc.to_dict()}")

    # Check nutribot_metrics for user_profile event types
    metrics_docs = list(db.collection("nutribot_metrics").stream())
    user_profiles_in_metrics = []
    for doc in metrics_docs:
        d = doc.to_dict()
        if d.get("event_type") == "user_profile":
            user_profiles_in_metrics.append(d)

    print(f"\nUser Profiles in 'nutribot_metrics' (event_type == 'user_profile'): {len(user_profiles_in_metrics)}")
    if user_profiles_in_metrics:
        print("Sample User Profile record in 'nutribot_metrics':")
        sample = user_profiles_in_metrics[0]
        print(json.dumps({k: str(v) for k, v in sample.items()}, indent=4))

    print("\n🔍 **Codebase Diagnosis Summary**:")
    print("• `app.py` writes user welcome screen survey responses (goal, age, gender)")
    print("  via `log_interaction('user_profile', ...)` directly to the 'nutribot_metrics' collection.")
    print("• The 'users' collection is currently unused / unwritten by the web app, containing only a single template document.")
    print("• Therefore, user profile data IS being captured, but inside 'nutribot_metrics' under `event_type: user_profile`.\n")

    # ----------------------------------------------------
    # PART 4: EARLIEST & LATEST TIMESTAMP / FULL DATE RANGE
    # ----------------------------------------------------
    print("==================================================")
    print("4. FULL DATE RANGE & TIMESTAMP SPAN ANALYSIS")
    print("==================================================")

    collections = ["nutribot_logs", "nutribot_metrics"]
    all_timestamps = []

    for col in collections:
        docs = db.collection(col).stream()
        timestamps = []
        for d in docs:
            dt = parse_timestamp(d.to_dict().get("timestamp"))
            if dt:
                timestamps.append(dt)
                all_timestamps.append(dt)

        if timestamps:
            timestamps.sort()
            earliest = timestamps[0]
            latest = timestamps[-1]
            span = latest - earliest
            print(f"Collection '{col}':")
            print(f"  • Earliest Entry: {earliest.isoformat()}")
            print(f"  • Latest Entry:   {latest.isoformat()}")
            print(f"  • Date Range:     {earliest.strftime('%Y-%m-%d %H:%M:%S UTC')} to {latest.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  • Total Time Span: {format_span(span)}\n")
        else:
            print(f"Collection '{col}': No valid timestamps found.\n")

    if all_timestamps:
        all_timestamps.sort()
        global_earliest = all_timestamps[0]
        global_latest = all_timestamps[-1]
        global_span = global_latest - global_earliest

        print("--------------------------------------------------")
        print("OVERALL DATABASE DATE RANGE (COMBINED):")
        print(f"  • Global Earliest Entry: {global_earliest.isoformat()}")
        print(f"  • Global Latest Entry:   {global_latest.isoformat()}")
        print(f"  • Global Date Range:     {global_earliest.strftime('%Y-%m-%d %H:%M:%S UTC')} to {global_latest.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  • Global Time Span:      {format_span(global_span)}")
        print("--------------------------------------------------")

if __name__ == "__main__":
    run_full_diagnosis()
