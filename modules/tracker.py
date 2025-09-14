import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

load_dotenv()

MAX_JOB_AGE_DAYS = 90

def load_processed_jobs():
    kv_url = os.getenv("KV_STORE_URL")
    if not kv_url:
        print("⚠️ KV_STORE_URL is not set in .env file. Cannot track jobs.")
        return set(), []

    try:
        response = requests.get(kv_url)
        if response.status_code == 200:
            job_records = response.json()
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
                        continue

            recent_urls = {job['url'] for job in recent_jobs}
            print(f"Tracker: Loaded {len(job_records)} records, {len(recent_urls)} are recent.")
            return recent_urls, recent_jobs
        
        elif response.status_code == 404:
            print("Tracker is empty. Starting fresh.")
            return set(), []
        else:
            print(f"❌ Error loading jobs from cloud tracker (Status {response.status_code}): {response.text}")
            return set(), []
    except requests.RequestException as e:
        print(f"❌ Network error while loading jobs: {e}")
        return set(), []

def update_processed_jobs(newly_processed_urls, existing_recent_jobs):
    kv_url = os.getenv("KV_STORE_URL")
    if not kv_url:
        print("⚠️ KV_STORE_URL is not set. Cannot update tracker.")
        return

    print(f"📚 Saving {len(newly_processed_urls)} newly processed jobs to the cloud tracker...")
    
    processed_jobs_map = {job['url']: job for job in existing_recent_jobs}

    for url in newly_processed_urls:
        processed_jobs_map[url] = {'url': url, 'added_at': datetime.now().isoformat()}
    
    try:
        response = requests.post(kv_url, json=list(processed_jobs_map.values()))
        
        if response.status_code == 200:
            print("✅ Cloud job tracker updated successfully.")
        else:
            print(f"❌ Error updating cloud tracker (Status {response.status_code}): {response.text}")
    except requests.RequestException as e:
        print(f"❌ Network error while updating tracker: {e}")