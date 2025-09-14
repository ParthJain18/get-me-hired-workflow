import os
import jobspy
import pandas as pd
from config import (
    SEARCH_TERMS, LOCATIONS, JOB_SITES, RESULTS_WANTED, COUNTRY_INDEED, USE_PROXIES_IN_WORKFLOW
)

ZYTE_CERT_PATH = "zyte-proxy-ca.crt"

def run_scraper():
    print("Starting job scrape...")

    proxies_to_use = []
    zyte_api_key = os.getenv('ZYTE_API_KEY')
    if USE_PROXIES_IN_WORKFLOW and zyte_api_key:
        print("🚀 Found ZYTE_API_KEY. Configuring Zyte Smart Proxy.")
        proxies_to_use = [f"https://{zyte_api_key}:@api.zyte.com:8014"]
        if os.path.exists(ZYTE_CERT_PATH):
            ca_cert_to_use = ZYTE_CERT_PATH
            print(f"🔒 Found Zyte certificate at '{ZYTE_CERT_PATH}'.")
        else:
            print(f"⚠️ Could not find Zyte certificate at '{ZYTE_CERT_PATH}'. SSL errors may occur.")

    else:
        print("⚠️ No proxy configured. Running with local/runner IP.")

    all_jobs_df = pd.DataFrame()
    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            print(f"Scraping for '{term}' in '{location}'...")
            jobs_df = jobspy.scrape_jobs(
                site_name=JOB_SITES,
                search_term=term,
                location=location,
                results_wanted=RESULTS_WANTED,
                country_indeed=COUNTRY_INDEED,
                proxies=proxies_to_use,
                hours_old=168,
                # ca_cert=ca_cert_to_use
            )
            if jobs_df is not None and not jobs_df.empty:
                all_jobs_df = pd.concat([all_jobs_df, jobs_df], ignore_index=True)
    
    print(all_jobs_df.head)

    all_jobs_df.drop_duplicates(subset=['job_url'], inplace=True)
    all_jobs_df['id'] = all_jobs_df['job_url'].apply(lambda x: hash(x))
    print(f"Scraped a total of {len(all_jobs_df)} unique jobs.")
    return all_jobs_df.to_dict('records')
