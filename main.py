import os
import time
import json
import hashlib
import random
import pandas as pd
from dotenv import load_dotenv
from config import (
    SOURCE_RESUME_PATH, PARSED_RESUME_PATH, GEMINI_TOP_N,
    MIN_EXPERIENCE_YEARS, MAX_EXPERIENCE_YEARS, MIN_SALARY_INR,
    USE_ENHANCED_DATA_FETCHING, COSINE_FILTER_TOP_N
)
from modules.scraper import run_scraper
from modules.nlp_processor import filter_jobs_by_similarity
from modules.gemini_client import (
    parse_resume, get_job_rankings, generate_latex_resume,
    classify_experience_level, condense_latex_resume
)
from modules.resume_generator import create_resume_pdf, get_pdf_page_count
from modules.email_module import send_notification
from modules.tracker import load_processed_jobs, update_processed_jobs
from keyword_filter import filter_jobs_by_experience, is_salary_over_min
from modules.data_fetcher import fetch_structured_job_data


def setup_resume_for_matching():
    try:
        with open(SOURCE_RESUME_PATH, 'rb') as f:
            source_bytes = f.read()
        current_source_hash = hashlib.md5(source_bytes).hexdigest()
        source_latex = source_bytes.decode('utf-8')
    except FileNotFoundError:
        print(
            f"❌ Error: Source resume file not found at '{SOURCE_RESUME_PATH}'. Please create it.")
        return None

    cached_data = {}
    if os.path.exists(PARSED_RESUME_PATH):
        with open(PARSED_RESUME_PATH, 'r', encoding='utf-8') as f:
            try:
                cached_data = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Warning: Could not decode parsed_resume.json. Will re-parse.")

    cached_hash = cached_data.get("source_hash")
    if current_source_hash == cached_hash:
        print("✅ Parsed resume is up-to-date (source hash matches).")
        return cached_data.get("parsed_text")
    else:
        print(
            f"Source resume '{SOURCE_RESUME_PATH}' has changed. Parsing for matching...")
        parsed_text = parse_resume(source_latex)
        if parsed_text:
            new_data = {
                "source_hash": current_source_hash,
                "parsed_text": parsed_text
            }
            with open(PARSED_RESUME_PATH, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2)
            print("✅ Resume parsed and new hash saved.")
            return parsed_text
        else:
            print("❌ Failed to parse resume. Using previous version if available.")
            return cached_data.get("parsed_text")


def apply_filters(jobs_list):
    if not jobs_list:
        return []

    # Salary Filter
    if MIN_SALARY_INR > 0:
        print(f"\n--- Starting Salary Filter (Min: ₹{MIN_SALARY_INR:,}) ---")
        df = pd.DataFrame(jobs_list)
        required_cols = {'min_amount': pd.NA, 'max_amount': pd.NA, 'interval': 'yearly', 'currency': 'INR'}
        for col, default in required_cols.items():
            if col not in df.columns:
                df[col] = default
            # Use fillna on the series and assign it back
            df[col] = df[col].fillna(default)


        salary_mask = df.apply(is_salary_over_min, axis=1, min_annual_salary_inr=MIN_SALARY_INR)
        jobs_list = df[salary_mask].to_dict('records')
        print(f"--- Salary filter finished. {len(jobs_list)} jobs remain. ---")
        if not jobs_list:
            print("--- Pipeline finished: No jobs match your salary criteria. ---")
            return []

    # Experience Filter
    jobs_list = filter_jobs_by_experience(jobs_list, MAX_EXPERIENCE_YEARS)
    if not jobs_list:
        print("--- Pipeline finished: No jobs match your experience criteria. ---")
        return []

    return jobs_list


def main():
    print("--- Starting AI Job Application Assistant ---")
    load_dotenv()

    processed_job_urls, existing_recent_records = load_processed_jobs()
    print(
        f"🔍 Found {len(processed_job_urls)} previously processed jobs in the tracker.")

    resume_text_for_matching = setup_resume_for_matching()
    if not resume_text_for_matching:
        return

    scraped_jobs = run_scraper()
    if not scraped_jobs:
        return

    new_jobs = [job for job in scraped_jobs if job.get('job_url') not in processed_job_urls]
    print(f"✨ Found {len(new_jobs)} new jobs to process after filtering duplicates.")
    if not new_jobs:
        print("--- Pipeline finished: No new jobs found. ---")
        return

    if USE_ENHANCED_DATA_FETCHING:
        print("\n--- Running Enhanced Workflow with Zyte API ---")

        # TODO: REMOVE later
        ENHANCED_WORKFLOW_SAMPLE_SIZE = 10
        if len(new_jobs) > ENHANCED_WORKFLOW_SAMPLE_SIZE:
            print(f"Selecting a random sample of {ENHANCED_WORKFLOW_SAMPLE_SIZE} from {len(new_jobs)} new jobs.")
            jobs_to_process_sample = random.sample(new_jobs, ENHANCED_WORKFLOW_SAMPLE_SIZE)
        else:
            print(f"Processing all {len(new_jobs)} new jobs (less than sample size).")
            jobs_to_process_sample = new_jobs

        jobspy_data_map = {job.get('job_url'): job for job in jobs_to_process_sample if job.get('job_url')}
        urls_to_fetch = list(jobspy_data_map.keys())

        zyte_fetched_jobs = fetch_structured_job_data(urls_to_fetch) # type: ignore

        print("\n--- Comparing jobspy data (Before) vs. Zyte data (After) ---")
        for zyte_job in zyte_fetched_jobs:
            url = zyte_job.get('job_url')
            jobspy_job = jobspy_data_map.get(url, {})
            print("-" * 70)
            print(f"URL: {url}")
            print(f"  [Before] jobspy Title:    {jobspy_job.get('title', 'N/A')}")
            print(f"  [After]  Zyte Title:       {zyte_job.get('title', 'N/A')}")
            print(f"  [Before] jobspy Company:   {jobspy_job.get('company', 'N/A')}")
            print(f"  [After]  Zyte Company:     {zyte_job.get('company', 'N/A')}")
            print(f"  [Before] jobspy Location:  {jobspy_job.get('location', 'N/A')}")
            print(f"  [After]  Zyte Location:    {zyte_job.get('location', 'N/A')}")
            print(f"  [Before] jobspy Salary:    {jobspy_job.get('salary', 'N/A')}")
            print(f"  [After]  Zyte Salary:      {zyte_job.get('salary', 'N/A')}")
            print(f"  [Before] jobspy Posted:    {jobspy_job.get('date_posted', 'N/A')}")
            print(f"  [After]  Zyte Posted:      {zyte_job.get('date_posted', 'N/A')}")
        print("-" * 70)

        jobs_to_filter = zyte_fetched_jobs
    else:
        print("\n--- Running Original Workflow with jobspy ---")
        jobs_to_filter = new_jobs

    filtered_jobs = apply_filters(jobs_to_filter)
    if not filtered_jobs:
        return

    print("\n--- Pre-filtering with Cosine Similarity ---")
    jobs_for_ranking = filter_jobs_by_similarity(filtered_jobs, resume_text_for_matching)
    if not jobs_for_ranking:
        return

    jobs_to_rank = jobs_for_ranking[:COSINE_FILTER_TOP_N]
    print(f"Sending top {len(jobs_to_rank)} jobs for Gemini ranking.")

    gemini_rankings = get_job_rankings(jobs_to_rank, resume_text_for_matching)
    if not gemini_rankings or 'ranked_jobs' not in gemini_rankings:
        return

    try:
        with open(SOURCE_RESUME_PATH, 'r', encoding='utf-8') as f:
            source_latex = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Source resume file '{SOURCE_RESUME_PATH}' not found.")
        return

    ranked_jobs_info = gemini_rankings['ranked_jobs']
    jobs_to_process = ranked_jobs_info[:GEMINI_TOP_N]
    original_jobs_map = {str(job['id']): job for job in jobs_for_ranking}
    results_list = []

    for i, rank_info in enumerate(jobs_to_process):
        print(f"\n--- Processing Job {i+1} of {len(jobs_to_process)} ---")
        full_job_details = original_jobs_map.get(rank_info['id'])
        if not full_job_details:
            print(f"⚠️ Could not find full details for job ID {rank_info['id']}. Skipping.")
            continue

        full_job_details['match_reason'] = rank_info.get('match_reason', 'N/A')
        modified_latex = generate_latex_resume(source_latex, full_job_details)
        generation_failed = False
        final_latex = modified_latex if modified_latex else source_latex
        if not modified_latex:
            print(f"⚠️ AI resume generation failed for '{str(full_job_details.get('title', 'N/A'))}'.")
            generation_failed = True

        pdf_path = create_resume_pdf(final_latex, full_job_details)
        page_count = get_pdf_page_count(pdf_path)
        print(f"   📄 Compiled PDF has {page_count} page(s).")

        if page_count > 1:
            print(f"   ⚠️ Resume is {page_count} pages. Attempt 2: Condensing content...")
            condensed_latex = condense_latex_resume(final_latex)
            if condensed_latex:
                final_latex = condensed_latex
                pdf_path = create_resume_pdf(final_latex, full_job_details)
                final_page_count = get_pdf_page_count(pdf_path)
                print(f"   ✅ Condensing successful. Final PDF has {final_page_count} page(s).")
                if final_page_count > 1:
                    print("   ❌ Condensing failed to reduce to one page.")
            else:
                print("   ❌ AI condensing failed.")
                generation_failed = True

        if pdf_path:
            results_list.append({
                'job_details': full_job_details,
                'pdf_path': pdf_path,
                'generation_failed': generation_failed
            })
        else:
            print(f"❌ Critical Error: Could not generate PDF for '{str(full_job_details.get('title', 'N/A'))}'.")

    if results_list:
        send_notification(results_list)
        newly_processed_urls = [res['job_details']['job_url'] for res in results_list]
        update_processed_jobs(newly_processed_urls, existing_recent_records)
    else:
        print("--- No resumes were successfully generated. ---")

    print("\n--- AI Job Application Assistant finished successfully! ---")


if __name__ == "__main__":
    main()