SEARCH_TERMS = ["Software Development Engineer", "Backend Engineer", "AI ML Engineer", "Data Science"]
LOCATIONS = ["Mumbai", "Bangalore", "Remote"]
MIN_SALARY_INR = 800000  # Example: 8 Lakhs per annum
HOURS_PER_YEAR = 2080  # 40 hours/week * 52 weeks
USD_TO_INR_RATE = 85.0  # Example conversion rate, adjust as needed
MIN_EXPERIENCE_YEARS = 0
MAX_EXPERIENCE_YEARS = 1

JOB_SITES = ["linkedin", "indeed", "google", "naukri"]  # Sites supported by JobSpy
TARGET_LOCATIONS = [loc.lower() for loc in LOCATIONS]
COUNTRY_INDEED = "India"  # Country for Indeed searches
# Set to True to enable proxy usage if PROXY_LIST is set in .env
USE_PROXIES_IN_WORKFLOW = False
USE_ENHANCED_DATA_FETCHING = True

RESULTS_WANTED = 30
MAX_JOB_AGE_DAYS = 7
COSINE_FILTER_TOP_N = 30
GEMINI_TOP_N = 20
MODEL_NAME = "gemini-2.5-pro"
# Will be used to find the required experience level
CLASSIFICATION_MODEL_NAME = "gemini-2.0-flash"
# Delay between Gemini 2.5 Pro API calls to avoid rate limits
API_CALL_DELAY_SECONDS = 20

SOURCE_RESUME_PATH = "source_resume.tex"
PARSED_RESUME_PATH = "parsed_resume.json"
OUTPUT_DIR = "generated_resumes"
PROCESSED_JOBS_PATH = "processed_jobs.json"

DELIVERY_METHOD = "email"
USER_MESSAGE = "Please prioritize SDE and AI ML related roles that suit my skills. Also, if the jobs aren't remote, prefer those in Mumbai."