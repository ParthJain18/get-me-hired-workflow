import re

def filter_jobs_by_experience(jobs_list, max_experience_years=2):
    print(f"🔍 Filtering jobs for max {max_experience_years} years experience using enhanced logic...")
    
    senior_keywords = [
        'senior', 'sr.', 'sr ', 'lead', 'principal', 'staff', 'architect', 
        'manager', 'head of', 'director', 'vp', 'vice president', 'chief',
        'level 3', 'level 4', 'level 5', 'l3', 'l4', 'l5', 'iii', 'iv', 'v'
    ]
    
    def has_senior_keywords(title):
        text_to_check = title.lower()
        for keyword in senior_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_to_check):
                return True
        return False
    
    filtered_jobs = []
    skipped_count = 0

    for job in jobs_list:
        title = job.get('title', '')
        description = job.get('description', '')
        job_level = job.get('job_level', '').lower()
        experience_range = job.get('experience_range') # e.g., (0, 2)
        job_type = job.get('job_type', '').lower()

        if job_type == 'internship' or job_level == 'entry level':
            print(f"  ✅ Kept (Entry/Intern): '{title}'")
            filtered_jobs.append(job)
            continue
            
        if job_level and any(level in job_level for level in ['senior', 'lead', 'director', 'manager', 'principal']):
            print(f"  ❌ Skipped (Structured): '{title}' - Level is '{job.get('job_level')}'")
            skipped_count += 1
            continue
            
        if experience_range and isinstance(experience_range, tuple) and len(experience_range) == 2:
            min_req, max_req = experience_range
            if min_req > max_experience_years:
                print(f"  ❌ Skipped (Structured): '{title}' - Requires {min_req}-{max_req} years")
                skipped_count += 1
                continue

        if has_senior_keywords(title):
            print(f"  ❌ Skipped (Keyword): '{title}' - Contains senior keywords in title")
            skipped_count += 1
            continue

        desc_min_exp = extract_experience_from_text(description)
        if desc_min_exp > max_experience_years:
            print(f"  ❌ Skipped (Regex): '{title}' - Requires {desc_min_exp}+ years in description")
            skipped_count += 1
            continue
            
        filtered_jobs.append(job)

    print(f"🎯 Enhanced filtering complete: {skipped_count} jobs filtered out, {len(filtered_jobs)} remain.")
    return filtered_jobs

def should_use_gemini_classification(jobs_count, threshold=20):
    """
    Decide whether to use Gemini classification based on remaining job count.
    For small numbers, keyword filtering might be sufficient.
    """
    if jobs_count <= threshold:
        return True  # Worth using Gemini for precise classification
    else:
        print(f"⚠️  {jobs_count} jobs remaining after keyword filter.")
        print(f"   Consider making keyword filter stricter to reduce Gemini API calls.")
        return True  # You can change this to False to skip Gemini entirely

def filter_jobs_by_location(jobs_list, allowed_locations):
    """
    Strictly filters jobs to ensure their location is in the allowed list.
    Handles both string locations and the structured location dictionary from jobspy.
    """
    print(f"📍 Applying strict location filter for: {allowed_locations}")
    
    # Normalize allowed locations for case-insensitive comparison
    allowed_lower = [loc.lower() for loc in allowed_locations]
    
    filtered_jobs = []
    skipped_count = 0
    
    for job in jobs_list:
        job_location_obj = job.get('location') # e.g., {'city': 'Pune', 'state': 'Maharashtra'}
        
        if isinstance(job_location_obj, dict):
            city = (job_location_obj.get('city') or "").lower()
            state = (job_location_obj.get('state') or "").lower()
            country = (job_location_obj.get('country') or "").lower()
            
            is_match = False
            for allowed_loc in allowed_lower:
                if allowed_loc in [city, state, country]:
                    is_match = True
                    break
            
            if is_match:
                filtered_jobs.append(job)
            else:
                skipped_count += 1
        
        # Fallback for older versions or if location is just a string
        elif isinstance(job_location_obj, str):
            if any(allowed_loc in job_location_obj.lower() for allowed_loc in allowed_lower):
                filtered_jobs.append(job)
            else:
                skipped_count += 1
        else:
            # If location is missing, we might skip it or keep it based on preference
            skipped_count += 1
            
    print(f"🎯 Location filtering complete: {skipped_count} jobs removed, {len(filtered_jobs)} remain.")
    return filtered_jobs

# Alternative: Even stricter keyword filter for entry-level positions
def filter_for_entry_level_jobs(jobs_list):
    """
    More aggressive filtering to find only entry-level/junior positions
    """
    print("🎯 Filtering for entry-level positions only...")
    
    # Positive keywords for entry-level positions
    entry_level_keywords = [
        'junior', 'jr.', 'jr ', 'entry level', 'entry-level', 'graduate', 
        'intern', 'trainee', 'fresher', 'new grad', 'associate',
        'level 1', 'level 2', 'level i', 'level ii', 'l1', 'l2',
        'starting', 'beginner', 'recent graduate'
    ]
    
    # Experience ranges that are acceptable (max 2 years)
    acceptable_experience_patterns = [
        r'\b0-2\s*years?\b', r'\b1-2\s*years?\b', r'\b0-1\s*years?\b',
        r'\bfresh(er)?\b', r'\bno experience\b', r'\bentry.?level\b'
    ]
    
    entry_level_jobs = []
    
    for job in jobs_list:
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        text_to_check = f"{title} {description}"
        
        # Check for entry-level indicators
        has_entry_keywords = any(keyword in text_to_check for keyword in entry_level_keywords)
        has_acceptable_exp = any(re.search(pattern, text_to_check, re.IGNORECASE) 
                               for pattern in acceptable_experience_patterns)
        
        # Avoid senior keywords
        senior_terms = ['senior', 'sr.', 'lead', 'principal', 'manager', 'architect']
        has_senior_terms = any(term in text_to_check for term in senior_terms)
        
        # Check explicit experience requirements
        desc_min_exp = extract_experience_from_text(description)
        
        if (has_entry_keywords or has_acceptable_exp) and not has_senior_terms and desc_min_exp <= 2:
            entry_level_jobs.append(job)
            print(f"  ✅ Entry-level match: '{job.get('title')}'")
        else:
            print(f"  ❌ Not entry-level: '{job.get('title')}'")
    
    print(f"🎯 Entry-level filtering: Found {len(entry_level_jobs)} suitable positions")
    return entry_level_jobs

def extract_experience_from_text(text):
    """Helper function to extract minimum experience from text"""
    if not text:
        return 0
        
    experience_phrases = [
        r'\b(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)\b',
        r'\b(\d+)-(\d+)\s*years?\s*(of\s*)?(experience|exp)\b',
        r'\bminimum\s*(\d+)\s*years?\b',
        r'\bat least\s*(\d+)\s*years?\b',
    ]
    
    text_lower = text.lower()
    min_exp = 0
    
    for pattern in experience_phrases:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                numbers = [int(x) for x in match if x.isdigit()]
                if numbers:
                    min_exp = max(min_exp, min(numbers))
            elif str(match).isdigit():
                min_exp = max(min_exp, int(match))
    
    return min_exp
