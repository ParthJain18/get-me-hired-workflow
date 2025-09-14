import os
import time
from dotenv import load_dotenv
from config import SOURCE_RESUME_PATH, PARSED_RESUME_PATH, GEMINI_TOP_N, API_CALL_DELAY_SECONDS, MIN_EXPERIENCE_YEARS, MAX_EXPERIENCE_YEARS, MIN_SALARY_INR
from modules.scraper import run_scraper
from modules.nlp_processor import filter_jobs_by_similarity
from modules.gemini_client import parse_resume, get_job_rankings, generate_latex_resume, classify_experience_level 
from modules.resume_generator import create_resume_pdf
from modules.email_module import send_notification
from modules.tracker import load_processed_jobs, update_processed_jobs

def setup_resume_for_matching():
    try:
        source_mod_time = os.path.getmtime(SOURCE_RESUME_PATH)
        parsed_mod_time = os.path.getmtime(PARSED_RESUME_PATH) if os.path.exists(PARSED_RESUME_PATH) else 0

        if source_mod_time > parsed_mod_time:
            print(f"Source resume '{SOURCE_RESUME_PATH}' is new or updated. Parsing for matching...")
            with open(SOURCE_RESUME_PATH, 'r', encoding='utf-8') as f:
                latex_source = f.read()
            
            parsed_text = parse_resume(latex_source)
            if parsed_text:
                with open(PARSED_RESUME_PATH, 'w', encoding='utf-8') as f:
                    f.write(parsed_text)
                return parsed_text
            else:
                print("❌ Failed to parse resume. Exiting.")
                return None
        else:
            print("Parsed resume is up-to-date.")
    except FileNotFoundError:
        print(f"❌ Error: Source resume file not found at '{SOURCE_RESUME_PATH}'. Please create it.")
        return None

    with open(PARSED_RESUME_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    print("--- Starting AI Job Application Assistant ---")
    load_dotenv()

    processed_job_urls, existing_recent_records = load_processed_jobs()
    print(f"🔍 Found {len(processed_job_urls)} previously processed jobs in the tracker.")

    # Step 2: Parse/Load Resume for Matching
    resume_text_for_matching = setup_resume_for_matching()
    if not resume_text_for_matching: return

    # Step 3: Scrape Jobs
    scraped_jobs = run_scraper()
    if not scraped_jobs: return

    # Step 4: Filter out already processed jobs
    new_jobs = [job for job in scraped_jobs if job.get('job_url') not in processed_job_urls]
    print(f"✨ Found {len(new_jobs)} new jobs to process after filtering duplicates.")
    if not new_jobs:
        print("--- Pipeline finished: No new jobs found. ---")
        return
    
    
    # Step 5: Classify and Filter
    if MIN_SALARY_INR > 0:
        print(f"\n--- Starting Salary Filter (Min: ₹{MIN_SALARY_INR:,}) ---")
        initial_count = len(new_jobs)
        
        def is_salary_match(job):
            min_salary = job.get('min_amount') or 0
            max_salary = job.get('max_amount') or 0
            
            try:
                min_salary = float(min_salary)
                max_salary = float(max_salary)
            except (ValueError, TypeError):
                return True

            if min_salary == 0 and max_salary == 0: return True
            if max_salary >= MIN_SALARY_INR or min_salary >= MIN_SALARY_INR: return True
            return False

        jobs_after_salary_filter = [job for job in new_jobs if is_salary_match(job)]
        print(f"--- Salary filter finished. {initial_count - len(jobs_after_salary_filter)} jobs removed. {len(jobs_after_salary_filter)} remain. ---")
        new_jobs = jobs_after_salary_filter
        if not new_jobs:
            print("--- Pipeline finished: No new jobs match your salary criteria. ---")
            return
        
    print("\n--- Starting Experience Level Classification ---")
    classified_and_filtered_jobs = []
    for i, job in enumerate(new_jobs):
        experience_data = classify_experience_level(job)
        
        # Check if the job's required experience range overlaps with your desired range
        if experience_data:
            job_min = experience_data.get('min_years', 99)
            job_max = experience_data.get('max_years', 99)
            
            is_match = max(MIN_EXPERIENCE_YEARS, job_min) <= min(MAX_EXPERIENCE_YEARS, job_max)
            
            if is_match:
                print(f"  ✅ Match found: '{job.get('title')}' requires {job_min}-{job_max} years. Adding to list.")
                job['min_years'] = job_min
                job['max_years'] = job_max
                classified_and_filtered_jobs.append(job)
            else:
                 print(f"  ❌ No match: '{job.get('title')}' requires {job_min}-{job_max} years. Skipping.")

        # Respect API rate limits
        if i < len(new_jobs) - 1:
            time.sleep(5)

    print(f"--- Experience classification finished. Found {len(classified_and_filtered_jobs)} jobs matching your experience range. ---")
    if not classified_and_filtered_jobs:
        print("--- Pipeline finished: No new jobs match your experience criteria. ---")
        return

    # Step 6: Pre-filter with Cosine Similarity
    filtered_jobs = filter_jobs_by_similarity(new_jobs, resume_text_for_matching)
    if not filtered_jobs: return

    # Step 7: Get Job Rankings from Gemini
    gemini_rankings = get_job_rankings(filtered_jobs, resume_text_for_matching)
    if not gemini_rankings or 'ranked_jobs' not in gemini_rankings: return

    # Step 8: Generate Resumes and Collect Results
    try:
        with open(SOURCE_RESUME_PATH, 'r', encoding='utf-8') as f:
            source_latex = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Source resume file '{SOURCE_RESUME_PATH}' not found.")
        return
        
    ranked_jobs = gemini_rankings['ranked_jobs']
    jobs_to_process = ranked_jobs[:GEMINI_TOP_N]
    original_jobs_map = {job['id']: job for job in filtered_jobs}
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
        latex_to_compile = modified_latex
        if not modified_latex:
            print(f"⚠️ AI resume generation failed for '{full_job_details.get('title')}'. Falling back to the original resume.")
            generation_failed = True
            latex_to_compile = source_latex
        pdf_path = create_resume_pdf(latex_to_compile, full_job_details)
        if pdf_path:
            results_list.append({
                'job_details': full_job_details,
                'pdf_path': pdf_path,
                'generation_failed': generation_failed
            })
        else:
            print(f"❌ PDF compilation failed for '{full_job_details.get('title')}'. This job will not be included in the email.")
        if i < len(jobs_to_process) - 1:
            print(f"🕒 Waiting for {API_CALL_DELAY_SECONDS} seconds to respect API rate limits...")
            time.sleep(API_CALL_DELAY_SECONDS)


    if results_list:
        send_notification(results_list)
        newly_processed_urls = [res['job_details']['job_url'] for res in results_list]
        update_processed_jobs(newly_processed_urls, existing_recent_records)
    else:
        print("--- No resumes were successfully generated, skipping notification and tracker update. ---")

    print("\n--- AI Job Application Assistant finished successfully! ---")

if __name__ == "__main__":
    main()