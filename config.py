SEARCH_TERMS = ["Software Development Engineer", "Backend Engineer", "AI ML Engineer", "AI Engineer"]
LOCATIONS = ["Mumbai, India", "Bangalore, India", "Pune, India", "Remote"]
MIN_SALARY_INR = 800000 # Example: 8 Lakhs per annum
MIN_EXPERIENCE_YEARS = 0
MAX_EXPERIENCE_YEARS = 2

JOB_SITES = ["linkedin", "indeed"] # Sites supported by JobSpy
COUNTRY_INDEED = "India" # Country for Indeed searches
USE_PROXIES_IN_WORKFLOW = True # Set to True to enable proxy usage if PROXY_LIST is set in .env

RESULTS_WANTED = 30
COSINE_FILTER_TOP_N = 20
GEMINI_TOP_N = 10
MODEL_NAME = "gemini-2.5-pro"
CLASSIFICATION_MODEL_NAME = "gemini-2.5-flash" # Will be used to find the required experience level
API_CALL_DELAY_SECONDS = 20 # Delay between Gemini 2.5 Pro API calls to avoid rate limits

SOURCE_RESUME_PATH = "source_resume.tex"
PARSED_RESUME_PATH = "parsed_resume.txt"
OUTPUT_DIR = "generated_resumes"
PROCESSED_JOBS_PATH = "processed_jobs.json"

DELIVERY_METHOD = "email"