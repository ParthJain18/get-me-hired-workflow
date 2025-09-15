SEARCH_TERMS = ["Software Development Engineer", "Backend Engineer", "AI ML Engineer", "Data Science"]
LOCATIONS = ["Mumbai", "Bangalore", "Remote"]
MIN_SALARY_INR = 800000 # Example: 8 Lakhs per annum
HOURS_PER_YEAR = 2080 # 40 hours/week * 52 weeks
USD_TO_INR_RATE = 85.0 # Example conversion rate, adjust as needed
MIN_EXPERIENCE_YEARS = 0
MAX_EXPERIENCE_YEARS = 1

JOB_SITES = ["linkedin", "indeed", "google", "naukri", "glassdoor"] # Sites supported by JobSpy
TARGET_LOCATIONS = [loc.lower() for loc in LOCATIONS]
COUNTRY_INDEED = "India" # Country for Indeed searches
USE_PROXIES_IN_WORKFLOW = False # Set to True to enable proxy usage if PROXY_LIST is set in .env
USE_ENHANCED_DATA_FETCHING = True

RESULTS_WANTED = 30
COSINE_FILTER_TOP_N = 20
GEMINI_TOP_N = 10
MODEL_NAME = "gemini-2.5-pro"
CLASSIFICATION_MODEL_NAME = "gemini-2.0-flash" # Will be used to find the required experience level
API_CALL_DELAY_SECONDS = 20 # Delay between Gemini 2.5 Pro API calls to avoid rate limits

SOURCE_RESUME_PATH = "source_resume.tex"
PARSED_RESUME_PATH = "parsed_resume.json"
OUTPUT_DIR = "generated_resumes"
PROCESSED_JOBS_PATH = "processed_jobs.json"

DELIVERY_METHOD = "email"