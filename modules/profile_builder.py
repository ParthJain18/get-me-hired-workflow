from config import TARGET_LOCATIONS, MIN_SALARY_INR, MIN_EXPERIENCE_YEARS, MAX_EXPERIENCE_YEARS, SEARCH_TERMS

def create_ideal_candidate_profile(resume_text: str) -> str:
    """
    Generates a detailed text profile combining resume skills and config preferences.
    """
    
    # Format locations for readability
    if len(TARGET_LOCATIONS) > 1:
        locations_str = f"{', '.join(TARGET_LOCATIONS[:-1])}, or {TARGET_LOCATIONS[-1]}"
    else:
        locations_str = TARGET_LOCATIONS[0]

    # Format job titles
    job_titles = SEARCH_TERMS
    if len(job_titles) > 1:
        titles_str = f"{', '.join(job_titles[:-1])}, or {job_titles[-1]}"
    else:
        titles_str = job_titles[0]
        
    profile = f"""
An ideal candidate profile for a job search.
The candidate is seeking a position as a {titles_str}.
They are looking for roles with an experience requirement between {MIN_EXPERIENCE_YEARS} and {MAX_EXPERIENCE_YEARS} years.
The preferred locations are {locations_str}.
The target minimum annual salary is {MIN_SALARY_INR:,} INR.

The candidate's skills and background are summarized below:
---
{resume_text}
"""
    print("\n--- Generated Ideal Candidate Profile for Matching ---")
    print(profile)
    return profile