import os
import time
import json
import hashlib
import pandas as pd
from dotenv import load_dotenv
from config import (
    SOURCE_RESUME_PATH, PARSED_RESUME_PATH, GEMINI_TOP_N,
    MIN_EXPERIENCE_YEARS, MAX_EXPERIENCE_YEARS, MIN_SALARY_INR,
    TARGET_LOCATIONS # Import your new config
)
from modules.scraper import run_scraper
from modules.nlp_processor import filter_jobs_by_similarity
from modules.gemini_client import (
    parse_resume, get_job_rankings, generate_latex_resume,
    condense_latex_resume
)
from modules.resume_generator import create_resume_pdf, get_pdf_page_count
from modules.email_module import send_notification
from modules.tracker import load_processed_jobs, update_processed_jobs
from modules.profile_builder import create_ideal_candidate_profile
from keyword_filter import filter_jobs_by_experience, is_salary_over_min


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

def filter_jobs_by_location(jobs: list[dict], target_locations: list[str]) -> list[dict]:
    """Filters jobs based on a list of target location keywords."""
    print(f"\n--- Starting Location Filter (Targets: {', '.join(target_locations)}) ---")
    initial_count = len(jobs)
    filtered = []
    
    for job in jobs:
        job_location = job.get('location')
        if not job_location or pd.isna(job_location):
            filtered.append(job)
            continue
        
        job_location_lower = str(job_location).lower()
        if any(target in job_location_lower for target in target_locations):
            filtered.append(job)
            
    print(f"--- Location filter finished. {initial_count - len(filtered)} jobs removed. {len(filtered)} remain. ---")
    return filtered


def apply_filters(jobs_list: list[dict]) -> list[dict]:
    """Applies location, salary, and experience filters to a list of jobs."""
    if not jobs_list:
        return []

    # --- Step 1: Location Filter ---
    filtered_jobs = filter_jobs_by_location(jobs_list, TARGET_LOCATIONS)
    if not filtered_jobs:
        return []

    # --- Step 2: Salary Filter ---
    if MIN_SALARY_INR > 0:
        print(f"\n--- Starting Salary Filter (Min: ₹{MIN_SALARY_INR:,}) ---")
        initial_count = len(filtered_jobs)
        df = pd.DataFrame(filtered_jobs)

        required_cols = {'min_amount': pd.NA, 'max_amount': pd.NA, 'interval': 'yearly', 'currency': 'INR'}
        for col, default_val in required_cols.items():
            if col not in df.columns: df[col] = default_val
            df[col] = df[col].apply(lambda x: pd.NA if pd.isnull(x) else x)
            df[col] = df[col].fillna(default_val)

        salary_mask = df.apply(is_salary_over_min, axis=1, min_annual_salary_inr=MIN_SALARY_INR)
        filtered_jobs = df[salary_mask].to_dict('records')
        print(f"--- Salary filter finished. {initial_count - len(filtered_jobs)} jobs removed. {len(filtered_jobs)} remain. ---")
        if not filtered_jobs: return []

    # --- Step 3: Experience Filter ---
    print("\n--- Starting Keyword-based Experience Filter ---")
    filtered_jobs = filter_jobs_by_experience(filtered_jobs, MAX_EXPERIENCE_YEARS)
    
    return filtered_jobs


def main():
    print("--- Starting AI Job Application Assistant ---")
    load_dotenv()

    processed_job_urls, existing_recent_records = load_processed_jobs()
    print(f"🔍 Found {len(processed_job_urls)} previously processed jobs in the tracker.")

    resume_text_for_matching = setup_resume_for_matching()
    if not resume_text_for_matching:
        return
    
    ideal_profile = create_ideal_candidate_profile(resume_text_for_matching)

    scraped_jobs = run_scraper()
    if not scraped_jobs:
        return

    new_jobs = [job for job in scraped_jobs if job.get('job_url') not in processed_job_urls]
    print(f"✨ Found {len(new_jobs)} new jobs to process after filtering duplicates.")
    if not new_jobs:
        print("--- Pipeline finished: No new jobs found. ---")
        return

    # Apply all pre-filters (Location, Salary, Experience)
    filtered_jobs = apply_filters(new_jobs)
    if not filtered_jobs:
        print("--- Pipeline finished: No jobs remain after filtering. ---")
        return

    # Pre-filter with Cosine Similarity
    print("\n--- Pre-filtering with Cosine Similarity ---")
    jobs_for_ranking = filter_jobs_by_similarity(filtered_jobs, ideal_profile)
    if not jobs_for_ranking:
        return

    # Rank the most relevant jobs with Gemini
    print("\n--- Ranking Top Jobs with Gemini ---")
    gemini_rankings = get_job_rankings(jobs_for_ranking, resume_text_for_matching)
    if not gemini_rankings or 'ranked_jobs' not in gemini_rankings:
        return

    # Generate Resumes and Collect Results
    try:
        with open(SOURCE_RESUME_PATH, 'r', encoding='utf-8') as f:
            source_latex = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Source resume file '{SOURCE_RESUME_PATH}' not found.")
        return

    ranked_jobs = gemini_rankings['ranked_jobs']
    jobs_to_process = ranked_jobs[:GEMINI_TOP_N]
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