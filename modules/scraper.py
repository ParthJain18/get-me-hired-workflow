import jobspy
import pandas as pd
from config import (
    SEARCH_TERMS, 
    LOCATIONS, 
    JOB_SITES, 
    RESULTS_WANTED, 
    COUNTRY_INDEED
)
import os

def run_scraper():
    print("Starting job scrape...")

    proxies_to_use = []
    zyte_api_key = os.getenv('ZYTE_API_KEY')
    if zyte_api_key:
        print("🚀 Found ZYTE_API_KEY. Configuring Zyte Smart Proxy.")
        proxies_to_use = [f"http://{zyte_api_key}:@proxy.zyte.com:8011"]
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
                proxies=proxies_to_use
            )
            if jobs_df is not None and not jobs_df.empty:
                all_jobs_df = pd.concat([all_jobs_df, jobs_df], ignore_index=True)

    all_jobs_df.drop_duplicates(subset=['job_url'], inplace=True)
    all_jobs_df['id'] = all_jobs_df['job_url'].apply(lambda x: hash(x))
    
    print(f"Scraped a total of {len(all_jobs_df)} unique jobs.")
    return all_jobs_df.to_dict('records')

# TODO: Add custom scrapers
