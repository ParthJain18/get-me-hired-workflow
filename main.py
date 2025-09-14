import os
import time
import json
import hashlib
from dotenv import load_dotenv
from config import SOURCE_RESUME_PATH, PARSED_RESUME_PATH, GEMINI_TOP_N, MIN_EXPERIENCE_YEARS, MAX_EXPERIENCE_YEARS, MIN_SALARY_INR
from modules.scraper import run_scraper
from modules.nlp_processor import filter_jobs_by_similarity
from modules.gemini_client import parse_resume, get_job_rankings, generate_latex_resume, classify_experience_level, condense_latex_resume
from modules.resume_generator import create_resume_pdf, get_pdf_page_count
from modules.email_module import send_notification
from modules.tracker import load_processed_jobs, update_processed_jobs
from keyword_filter import filter_jobs_by_experience, should_use_gemini_classification, filter_for_entry_level_jobs


def setup_resume_for_matching():
    PARSED_RESUME_JSON_PATH = "parsed_resume.json"

    try:
        with open(SOURCE_RESUME_PATH, 'rb') as f:
            source_bytes = f.read()
        current_source_hash = hashlib.md5(source_bytes).hexdigest()
        source_latex = source_bytes.decode('utf-8')

    except FileNotFoundError:
        print(f"❌ Error: Source resume file not found at '{SOURCE_RESUME_PATH}'. Please create it.")
        return None

    cached_data = {}
    if os.path.exists(PARSED_RESUME_JSON_PATH):
        with open(PARSED_RESUME_JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                cached_data = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Warning: Could not decode parsed_resume.json. Will re-parse.")

    cached_hash = cached_data.get("source_hash")

    if current_source_hash == cached_hash:
        print("✅ Parsed resume is up-to-date (source hash matches).")
        return cached_data.get("parsed_text")
    else:
        print(f"Source resume '{SOURCE_RESUME_PATH}' has changed. Parsing for matching...")
        parsed_text = parse_resume(source_latex)
        if parsed_text:
            new_data = {
                "source_hash": current_source_hash,
                "parsed_text": parsed_text
            }
            with open(PARSED_RESUME_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2)
            print("✅ Resume parsed and new hash saved.")
            return parsed_text
        else:
            print("❌ Failed to parse resume. Using previous version if available.")
            return cached_data.get("parsed_text")
        

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
    
    keyword_filtered_jobs = filter_jobs_by_experience(new_jobs, MAX_EXPERIENCE_YEARS)

    if not keyword_filtered_jobs:
        print("--- Pipeline finished: No jobs match your experience criteria after keyword filtering. ---")
        return
    use_gemini = should_use_gemini_classification(len(keyword_filtered_jobs))
    
    if use_gemini:
        print("\n--- Starting Gemini Experience Level Classification ---")
        classified_and_filtered_jobs = []
        
        for i, job in enumerate(keyword_filtered_jobs):
            experience_data = classify_experience_level(job)
            
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
            if i < len(keyword_filtered_jobs) - 1:
                time.sleep(5)

        print(f"--- Gemini classification finished. Found {len(classified_and_filtered_jobs)} jobs matching your experience range. ---")
        
        if not classified_and_filtered_jobs:
            print("--- Pipeline finished: No jobs passed Gemini classification. ---")
            return
            
        final_filtered_jobs = classified_and_filtered_jobs
    else:
        print("--- Skipping Gemini classification, using keyword filtering results. ---")
        final_filtered_jobs = keyword_filtered_jobs

    print(f"--- Experience classification finished. Found {len(classified_and_filtered_jobs)} jobs matching your experience range. ---")
    if not classified_and_filtered_jobs:
        print("--- Pipeline finished: No new jobs match your experience criteria. ---")
        return

    # Step 6: Pre-filter with Cosine Similarity
    filtered_jobs = filter_jobs_by_similarity(final_filtered_jobs, resume_text_for_matching)
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
    original_jobs_map = {str(job['id']): job for job in filtered_jobs}
    results_list = []
    
    for i, rank_info in enumerate(jobs_to_process):
        print(f"\n--- Processing Job {i+1} of {len(jobs_to_process)} ---")
        full_job_details = original_jobs_map.get(rank_info['id'])
        if not full_job_details:
            print(f"⚠️ Could not find full details for job ID {rank_info['id']}. Skipping.")
            continue

        full_job_details['match_reason'] = rank_info.get('match_reason', 'N/A')

        # Step 1: Try AI tailoring
        modified_latex = generate_latex_resume(source_latex, full_job_details)
        generation_failed = False
        latex_to_compile = modified_latex if modified_latex else source_latex
        if not modified_latex:
            print(f"⚠️ AI resume generation failed for '{full_job_details.get('title')}'. Falling back to the original resume.")
            generation_failed = True

        # Step 2: Try PDF compilation
        pdf_path = create_resume_pdf(final_latex, full_job_details)
        page_count = get_pdf_page_count(pdf_path)
        print(f"   📄 Compiled PDF has {page_count} page(s).")

        # Step 3: Second Attempt (Condensing), if needed
        if page_count > 1:
            print(f"   ⚠️ Resume is {page_count} pages. Attempt 2: Condensing content...")
            condensed_latex = condense_latex_resume(final_latex)
            
            if condensed_latex:
                final_latex = condensed_latex
                # Re-compile the PDF with the condensed version
                pdf_path = create_resume_pdf(final_latex, full_job_details)
                final_page_count = get_pdf_page_count(pdf_path)
                print(f"   ✅ Condensing successful. Final PDF has {final_page_count} page(s).")
                if final_page_count > 1:
                    print("   ❌ Condensing failed to reduce to one page. Using the shortened version anyway.")
            else:
                print("   ❌ AI condensing failed. Using the two-page version as a fallback.")
                generation_failed = True

            # Step 4: Add result to list (this logic is now cleaner)
            if pdf_path:
                results_list.append({
                    'job_details': full_job_details,
                    'pdf_path': pdf_path,
                    'generation_failed': generation_failed
                })
            else:
                print(f"❌ Critical Error: Could not generate any PDF for '{full_job_details.get('title')}'. Skipping.")


    if results_list:
        send_notification(results_list)
        newly_processed_urls = [res['job_details']['job_url'] for res in results_list]
        update_processed_jobs(newly_processed_urls, existing_recent_records)
    else:
        print("--- No resumes were successfully generated, skipping notification and tracker update. ---")

    print("\n--- AI Job Application Assistant finished successfully! ---")

if __name__ == "__main__":
    main()
