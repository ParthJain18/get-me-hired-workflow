import os
import json
import time
from google import genai
from google.genai import types
from prompts import get_resume_parsing_prompt, get_ranking_prompt, get_latex_generation_prompt, get_experience_classification_prompt, get_condensing_prompt
from models.gemini_output_models import RankingResponse, ExperienceResponse
from dotenv import load_dotenv
from config import MODEL_NAME, CLASSIFICATION_MODEL_NAME

load_dotenv()

try:
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
except Exception as e:
    print(
        f"❌ Failed to initialize Gemini client. Ensure GEMINI_API_KEY is set. Error: {e}")
    client = None


def _call_gemini(prompt, response_schema=None, model_override=None):
    """Helper function to call the Gemini API, now with schema support."""
    if not client:
        print("❌ Gemini client not initialized.")
        return None

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            config = types.GenerateContentConfig()
            if response_schema:
                config.response_mime_type = 'application/json'
                config.response_schema = response_schema

            response = client.models.generate_content(
                model=model_override if model_override else MODEL_NAME,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "503" in error_str and "UNAVAILABLE" in error_str and "overloaded" in error_str:
                if attempt < max_retries:
                    print(f"Retrying in 10 seconds due to overload...")
                    time.sleep(10)
                    continue
            print(f"❌ Error communicating with Gemini: {e}")
            return None


def parse_resume(latex_source):
    print("🧠 Calling Gemini to parse resume for better matching...")
    prompt = get_resume_parsing_prompt(latex_source)
    parsed_text = _call_gemini(prompt)
    if parsed_text:
        print("✅ Resume parsed successfully.")
        return parsed_text.strip()
    return None


def get_job_rankings(jobs_list, resume_summary):
    print("✨ Calling Gemini for job ranking...")

    jobs_for_prompt = [
        {"id": job['id'], "title": job['title'], "company": job.get(
            'company', 'N/A'), "url": job.get('job_url', ''), "description": job.get('description', '')[:2000]}
        for job in jobs_list
    ]
    job_postings_json = json.dumps({"jobs": jobs_for_prompt}, indent=2)

    prompt = get_ranking_prompt(resume_summary, job_postings_json)

    response_text = _call_gemini(prompt, response_schema=RankingResponse)

    if not response_text:
        return None

    try:
        gemini_output = json.loads(response_text)
        print("✅ Received and parsed schema-validated JSON from Gemini.")
        return gemini_output
    except json.JSONDecodeError as e:
        print(
            f"❌ This should not happen with a response_schema, but failed to parse JSON: {e}")
        print(f"Received text: {response_text}")
        return None


def generate_latex_resume(latex_source, job):
    print(
        f"📝 Calling Gemini to generate resume for '{job.get('title')}' at '{job.get('company')}'...")
    prompt = get_latex_generation_prompt(
        latex_source,
        job.get('title', 'N/A'),
        job.get('company', 'N/A'),
        job.get('description', '')[:5000]
    )

    modified_latex = _call_gemini(prompt)
    if modified_latex:
        print("✅ Received tailored LaTeX source from Gemini.")
        return modified_latex.strip().replace('```latex', '').replace('```', '')
    return modified_latex

def condense_latex_resume(latex_source):
    prompt = get_condensing_prompt(latex_source)
    condensed_latex = _call_gemini(prompt)
    if condensed_latex:
        print("✅ Received condensed LaTeX source from Gemini.")
        return condensed_latex.strip().replace('```latex', '').replace('```', '')
    return None

def classify_experience_level(job):
    print(f"🧠 Classifying experience for '{job.get('title', 'N/A')}'...")

    description_snippet = job.get('description', '')
    prompt = get_experience_classification_prompt(
        job.get('title', ''), description_snippet)

    response_text = _call_gemini(
        prompt, response_schema=ExperienceResponse, model_override=CLASSIFICATION_MODEL_NAME)

    if not response_text:
        return None

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        print(
            f"❌ Failed to parse experience classification JSON: {response_text}")
        return None
