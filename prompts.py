from config import GEMINI_TOP_N

def get_resume_parsing_prompt(latex_source):
    """Generates a prompt to parse a LaTeX resume into clean text."""
    return f"""
    You are an expert resume parser. Analyze the following LaTeX resume source code.
    Extract all meaningful text content, including professional summaries, work experience (company, title, dates, responsibilities, technologies), education, and skills.
    Exclude all LaTeX commands and formatting. Combine all the extracted text into a single, clean, comprehensive text block that can be used for NLP analysis.
    Do not exclude any relevant information from the resume.

    **LaTeX Source:**
    ```latex
    {latex_source}
    ```

    **Output:**
    Return only the clean text block.
    """

def get_ranking_prompt(resume_summary, job_postings_json):
    """Generates a prompt for Gemini to rank jobs."""
    return f"""
    You are an expert career coach AI. Your task is to analyze my professional summary and a list of pre-filtered job descriptions to find the best-fit roles.

    **My Professional Summary (extracted from my resume):**
    "{resume_summary}"

    **Pre-filtered Job Postings (JSON format):**
    {job_postings_json}

    **Your Task:**
    Deeply analyze the jobs against my summary and rank the top {GEMINI_TOP_N} absolute best matches for me.
    """

def get_latex_generation_prompt(latex_source, job_title, job_company, job_description):
    """Generates a prompt for Gemini to tailor and return a full LaTeX resume."""
    return f"""
    You are a world-class career coach and an expert in LaTeX resume formatting.
    Your task is to tailor my resume for a specific job application.

    **My Original LaTeX Resume:**
    ```latex
    {latex_source}
    ```

    **The Job I'm Applying For:**
    - **Title:** {job_title}
    - **Company:** {job_company}
    - **Description:** {job_description}

    **Your Instructions:**
    1.  **Modify the Professional Summary:** Rewrite the summary section (typically at the top) to be 2-3 sentences long, directly targeting the key requirements in the job description.
    2.  **Refine the Skills Section:** Identify the 5-7 most critical skills or technologies mentioned in the job description and ensure they are prominently featured in my skills section. You may add or reorder skills.
    3.  **Preserve Formatting:** Do NOT alter the overall structure, layout, fonts, or formatting of my LaTeX document. The changes should be surgical and focused only on the content of the summary and skills.
    4.  **IMPORTANT - Ensure Valid LaTeX:** Pay close attention to the job description content you integrate. You MUST correctly escape any special LaTeX characters (e.g., replace `_` with `\\_`, `&` with `\\&`, `%` with `\\%`). The final output must be a fully compilable LaTeX document.
    
    **Output:**
    Return ONLY the complete, modified, and valid LaTeX source code for the new resume. Do not include any explanations, apologies, or markdown formatting.
    """

def get_experience_classification_prompt(job_title: str, job_description: str) -> str:
    return f"""
    You are an expert HR analyst. Your task is to analyze the following job posting and determine the required years of experience.

    **Job Title:** "{job_title}"
    **Job Description:**
    "{job_description}"

    **Your Task:**
    Based on the title and description, estimate the minimum and maximum years of professional experience required.
    - If a specific range is given (e.g., "5-7 years"), use that.
    - If only a minimum is given (e.g., "5+ years"), set max_years to 2 years above the minimum.
    - For "entry-level" or "new grad" roles, use 0 for min_years and 1 for max_years.
    - If no experience level is mentioned at all, return 0 for both.
    """
