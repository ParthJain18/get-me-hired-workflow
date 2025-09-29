import os
import jobspy
import pandas as pd
from datetime import datetime, timedelta
from config import (
    SEARCH_TERMS, LOCATIONS, JOB_SITES, RESULTS_WANTED, COUNTRY_INDEED, USE_PROXIES_IN_WORKFLOW,
    MAX_JOB_AGE_DAYS
)

ZYTE_CERT_PATH = "zyte-proxy-ca.crt"


def run_scraper():
    print("Starting job scrape...")

    proxies_to_use = []
    ca_cert_to_use = None
    zyte_api_key = os.getenv('ZYTE_API_KEY')
    if USE_PROXIES_IN_WORKFLOW and zyte_api_key:
        print("🚀 Found ZYTE_API_KEY. Configuring Zyte Smart Proxy.")
        proxies_to_use = [f"https://{zyte_api_key}:@api.zyte.com:8014"]
        if os.path.exists(ZYTE_CERT_PATH):
            ca_cert_to_use = ZYTE_CERT_PATH
            print(f"🔒 Found Zyte certificate at '{ZYTE_CERT_PATH}'.")
        else:
            print(
                f"⚠️ Could not find Zyte certificate at '{ZYTE_CERT_PATH}'. SSL errors may occur.")

    else:
        print("⚠️ No proxy configured. Running with local/runner IP.")

    hours_old_window = MAX_JOB_AGE_DAYS * 24
    print(
        f"⏱️ Restricting scrape to jobs from the last {MAX_JOB_AGE_DAYS} day(s) (~{hours_old_window} hours).")

    all_jobs_df = pd.DataFrame()
    physical_locations = [loc for loc in LOCATIONS if loc.lower() != 'remote']
    scrape_for_remote = 'remote' in [loc.lower() for loc in LOCATIONS]

    for term in SEARCH_TERMS:
        for location in physical_locations:
            print(f"Scraping for '{term}' in '{location}'...")
            jobs_df = jobspy.scrape_jobs(
                site_name=JOB_SITES,
                search_term=term,
                location=location,
                results_wanted=RESULTS_WANTED,
                country_indeed=COUNTRY_INDEED,
                proxies=proxies_to_use,
                hours_old=hours_old_window,
                ca_cert=ca_cert_to_use,
            )
            if jobs_df is not None and not jobs_df.empty:
                all_jobs_df = pd.concat(
                    [all_jobs_df, jobs_df], ignore_index=True)

        if scrape_for_remote:
            print(f"Scraping for REMOTE '{term}' jobs...")
            jobs_df = jobspy.scrape_jobs(
                site_name=JOB_SITES,
                search_term=term,
                is_remote=True,
                results_wanted=RESULTS_WANTED,
                country_indeed=COUNTRY_INDEED,
                proxies=proxies_to_use,
                hours_old=hours_old_window,
                ca_cert=ca_cert_to_use,
            )
            if jobs_df is not None and not jobs_df.empty:
                all_jobs_df = pd.concat(
                    [all_jobs_df, jobs_df], ignore_index=True)

    # all_jobs_df.to_csv("all_scraped_jobs.csv", index=False)
    if all_jobs_df.empty:
        print("❌ No jobs found after scraping.")
        return []

    all_jobs_df.drop_duplicates(subset=['job_url'], inplace=True)

    if 'date_posted' in all_jobs_df.columns:
        cutoff_timestamp = datetime.utcnow() - timedelta(days=MAX_JOB_AGE_DAYS)
        all_jobs_df['date_posted'] = pd.to_datetime(
            all_jobs_df['date_posted'], errors='coerce', utc=True)
        all_jobs_df['date_posted'] = all_jobs_df['date_posted'].dt.tz_localize(
            None)

        before_filter_count = len(all_jobs_df)
        unknown_dates = all_jobs_df['date_posted'].isna().sum()
        recent_jobs_mask = all_jobs_df['date_posted'].notna() & (
            all_jobs_df['date_posted'] >= cutoff_timestamp)
        all_jobs_df = all_jobs_df[recent_jobs_mask]

        dropped_for_age = before_filter_count - len(all_jobs_df)
        if dropped_for_age > 0:
            print(
                f"🧹 Removed {dropped_for_age} job(s) older than {MAX_JOB_AGE_DAYS} day(s).")
        if unknown_dates > 0:
            print(
                f"ℹ️ Dropped {unknown_dates} job(s) without a parseable 'date_posted' value to enforce recency.")
    else:
        print("⚠️ 'date_posted' column not found in results; relying solely on hours_old filter from JobSpy.")

    if all_jobs_df.empty:
        print("❌ No jobs remain after applying recency filters.")
        return []

    all_jobs_df['id'] = all_jobs_df['job_url'].apply(lambda x: str(hash(x)))
    print(f"✅ Scraped a total of {len(all_jobs_df)} unique jobs.")
    return all_jobs_df.to_dict('records')


if __name__ == "__main__":
    run_scraper()
