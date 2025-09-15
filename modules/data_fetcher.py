# Create a new file: modules/data_fetcher.py

import os
import requests
import time

def fetch_structured_job_data(job_urls: list[str]) -> list[dict]:
    """
    Uses the Zyte API to fetch structured data for a list of job URLs.
    """
    ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")
    if not ZYTE_API_KEY:
        print("? ZYTE_API_KEY not found in .env file. Cannot use enhanced fetching.")
        return []

    print(f"?? Starting enhanced data fetching for {len(job_urls)} URLs using Zyte API...")
    
    structured_jobs = []
    for i, url in enumerate(job_urls):
        print(f"   Fetching URL {i+1}/{len(job_urls)}: {url}")
        try:
            response = requests.post(
                "https://api.zyte.com/v1/extract",
                auth=(ZYTE_API_KEY, ''),
                json={
                    "url": url,
                    "jobPosting": True  # Use Zyte's automatic extraction for job postings
                }
            )
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

            data = response.json()
            if data.get("jobPosting"):
                # Map Zyte's output to our existing job format
                job_details = data["jobPosting"]
                mapped_job = {
                    'id': str(hash(url)),
                    'job_url': url,
                    'title': job_details.get('name'),
                    'company': job_details.get('hiringOrganization', {}).get('name'),
                    'location': job_details.get('jobLocation', {}).get('address'),
                    'description': job_details.get('description'),
                    # Add other fields as needed, checking if they exist
                }
                structured_jobs.append(mapped_job)
            else:
                print(f"   ?? Warning: 'jobPosting' data not found in response for {url}")

            # Add a small delay to be a good internet citizen
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"   ? Error fetching {url}: {e}")
            if "401" in str(e):
                print("   Authentication error. Check your ZYTE_API_KEY.")
            if "402" in str(e):
                print("   Payment Required. You may have exhausted your Zyte credits.")
                break # Stop processing if we're out of funds

    print(f"? Fetched structured data for {len(structured_jobs)} jobs.")
    return structured_jobs
