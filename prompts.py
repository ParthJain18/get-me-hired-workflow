from config import GEMINI_TOP_N, USER_MESSAGE


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
    {USER_MESSAGE}
    """


def get_resume_content_prompt(latex_source, job_title, job_company, job_description):
    """Generates a prompt requesting JSON snippets for tailored resume content."""
    return f"""
        You are a world-class career coach and resume strategist. Tailor the highlighted content of my resume for a specific job opening.

        **Base Resume (LaTeX Source):**
        ```latex
        {latex_source}
        ```

        **Target Role:**
        - Title: {job_title}
        - Company: {job_company}
        - Description: {job_description}

        **Deliverables:**
        Return a JSON object with EXACTLY these keys:
        ```json
        {{
            "summary_bullets": ["..."],
            "keywords": ["..."],
            "highlight_bullets": ["..."]
        }}
        ```

        **Rules:**
        - Provide 2 to 3 concise summary bullets in "summary_bullets" emphasising fit for the job.
        - Include 6 to 8 high-impact, comma-free keyword phrases in "keywords". Prefer skills, tools, domains, or certifications mentioned in the job.
        - Provide 3 job-aligned achievement bullets in "highlight_bullets". Each must be <= 140 characters, start with a strong verb, and include measurable impact when possible.
        - Use plain text only. Do NOT return LaTeX syntax, markdown, or additional commentary.
        - Do not invent experience I do not have. Prioritize items supported by the base resume or clearly implied by the description.
        - Ensure all strings are unique, single-line, and free of surrounding quotes beyond JSON requirements.

        **Output:**
        Return only the JSON object—no markdown fences, explanations, or additional keys.
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


def get_condensing_prompt(failed_latex_source):
    """
    Generates a prompt specifically to shorten LaTeX that was too long.
    """
    return f"""
    You are an expert resume editor with a single task: reduce the length of the provided resume to ensure it fits on one page.

    **Critical: The provided LaTeX source code resulted in a two-page document, which is unacceptable.**

    **LaTeX Source to Fix:**
    ```latex
    {failed_latex_source}
    ```

    **Your Instructions:**
    1.  **Shorten Content:** Your primary goal is to reduce the overall text length by 10%.
    2.  **Be Ruthless with Edits:** Combine bullet points, rephrase sentences to be more concise, and remove less critical phrases or descriptions. Focus on preserving the most impactful achievements.
    3.  **Do NOT Change Formatting:** Do not alter the LaTeX structure, commands, packages, or document class. Only edit the text content within the existing structure.
    4.  **Return Valid LaTeX:** The output must be the complete, valid, and shortened LaTeX source code.

    **Output:**
    Return ONLY the complete, shortened, and valid LaTeX source code.
    """
