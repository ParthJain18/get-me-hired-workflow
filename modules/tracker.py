import os
import json
from datetime import datetime, timedelta

TRACKER_FILE = "processed_jobs.json"
MAX_JOB_AGE_DAYS = 90

def load_processed_jobs():
    """Loads job records from the local tracker file, filters out old ones, and returns recent URLs."""
    if not os.path.exists(TRACKER_FILE):
        print("Tracker file not found. Starting fresh.")
        return set(), []

    try:
        with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
            job_records = json.load(f)
        
        if not isinstance(job_records, list):
            return set(), [] # Handle empty or malformed data

        cutoff_date = datetime.now() - timedelta(days=MAX_JOB_AGE_DAYS)
        recent_jobs = []
        for job in job_records:
            if isinstance(job, dict) and 'added_at' in job:
                try:
                    added_date = datetime.fromisoformat(job['added_at'])
                    if added_date > cutoff_date:
                        recent_jobs.append(job)
                except (ValueError, TypeError):
                    continue # Skip records with bad date formats

        recent_urls = {job['url'] for job in recent_jobs}
        print(f"Tracker: Loaded {len(job_records)} records, {len(recent_urls)} are recent.")
        return recent_urls, recent_jobs

    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error reading tracker file: {e}. Starting fresh.")
        return set(), []

def update_processed_jobs(newly_processed_urls, existing_recent_jobs):
    """Updates the job map and saves it to the local tracker file."""
    print(f"📚 Saving {len(newly_processed_urls)} newly processed jobs to the tracker file...")
    
    processed_jobs_map = {job['url']: job for job in existing_recent_jobs}

    for url in newly_processed_urls:
        processed_jobs_map[url] = {'url': url, 'added_at': datetime.now().isoformat()}
    
    try:
        with open(TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(processed_jobs_map.values()), f, indent=2)
        print("✅ Local job tracker file updated successfully.")
    except IOError as e:
        print(f"❌ Error writing to tracker file: {e}")