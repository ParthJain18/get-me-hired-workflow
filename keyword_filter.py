import re

def filter_jobs_by_experience_keywords(jobs_list, max_experience_years=2):
    """
    Filter out jobs that are clearly for experienced professionals based on keywords
    in title and description before using Gemini classification.
    """
    print(f"🔍 Pre-filtering jobs using keyword analysis for max {max_experience_years} years experience...")
    
    # Keywords that typically indicate senior/experienced positions
    senior_keywords = [
        # Direct experience indicators
        'senior', 'sr.', 'sr ', 'lead', 'principal', 'staff', 'architect', 
        'manager', 'head of', 'director', 'vp', 'vice president', 'chief',
        
        # Level indicators
        'level 2', 'level 3', 'level 4', 'level 5', # Added level 2
        'level ii', 'level iii', 'level iv', 'level v', # Added level ii
        'grade 2', 'grade 3', 'grade 4', 'grade 5', # Added grade 2
        'l2', 'l3', 'l4', 'l5', # Added l2
        'ii', 'iii', 'iv', 'v',  # Added ii
        
        # Experience-heavy roles
        'tech lead', 'technical lead',
        'team lead', 'engineering lead', 'solution architect', 
        'technical architect', 'enterprise architect',
        
        # Management/leadership terms
        'people manager', 'engineering manager', 'delivery manager',
        'practice manager', 'engagement manager', 'program manager'
    ]
    
    # Keywords that suggest high experience requirements in descriptions
    experience_phrases = [
        r'\b(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)\b',  # "5+ years experience"
        r'\b(\d+)-(\d+)\s*years?\s*(of\s*)?(experience|exp)\b',  # "3-5 years experience"
        r'\bminimum\s*(\d+)\s*years?\b',  # "minimum 5 years"
        r'\bat least\s*(\d+)\s*years?\b',  # "at least 4 years"
        r'\b(\d+)\s*to\s*(\d+)\s*years?\b',  # "4 to 6 years"
    ]
    
    def extract_experience_from_text(text):
        """Extract minimum experience years from text using regex"""
        if not text:
            return 0
        if not isinstance(text, str):
            return 0
            
        text_lower = text.lower()
        min_exp = 0
        
        for pattern in experience_phrases:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle different tuple structures from different regex patterns
                    numbers = [int(x) for x in match if x.isdigit()]
                    if numbers:
                        min_exp = max(min_exp, min(numbers))
                elif match.isdigit():
                    min_exp = max(min_exp, int(match))
        
        return min_exp
    
    def has_senior_keywords(title, description=""):
            """Check if title or description contains senior-level keywords using whole word matching."""
            text_to_check = f"{title} {description}".lower()
            
            for keyword in senior_keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, text_to_check):
                    return True
            return False
        
    filtered_jobs = []
    skipped_count = 0
    
    for job in jobs_list:
        title = job.get('title', '')
        description = job.get('description', '')
        
        # Check for obvious senior keywords first
        if has_senior_keywords(title, description):
            skipped_count += 1
            print(f"  ❌ Keyword filter: '{title}' - contains senior keywords")
            continue
        
        # Check for explicit experience requirements
        desc_min_exp = extract_experience_from_text(description)
        if desc_min_exp > max_experience_years:
            skipped_count += 1
            print(f"  ❌ Experience filter: '{title}' - requires {desc_min_exp}+ years")
            continue
        
        # Job passed the filters
        filtered_jobs.append(job)
    
    print(f"🎯 Keyword filtering complete: {skipped_count} jobs filtered out, {len(filtered_jobs)} remain")
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
