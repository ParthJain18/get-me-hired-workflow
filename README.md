# Get Me Hired Workflow

An automated Python pipeline that scrapes job postings, uses a multi-stage filtering process to find the most relevant roles, and leverages the Gemini API to tailor your LaTeX resume for the top-ranked positions.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.


## 🤖 What It Does

This project automates the tedious parts of a job search. Instead of manually searching for jobs and customizing your resume for each application, this assistant does it for you. It runs a pipeline that:

1.  **Scrapes** new job postings from multiple sites.
2.  **Filters** them based on your salary, experience, and keywords.
3.  **Ranks** the filtered jobs for relevance against your resume using AI.
4.  **Tailors** your resume's content for the best matches.
5.  **Delivers** the generated PDF resumes to your email.

## ✨ Key Features

  - **Multi-Source Scraping**: Gathers job postings from LinkedIn, Indeed, Google, Naukri, and more using `jobspy`.
  - **Intelligent Multi-Stage Filtering**:
      - **Deduplication**: Tracks previously processed jobs to avoid duplicates.
      - **Salary & Experience**: Filters jobs based on your configured salary and experience levels.
      - **Keyword Analysis**: A fast, initial pass to remove obviously irrelevant senior-level roles.
      - **Cosine Similarity**: Pre-filters for jobs with descriptions that are mathematically most similar to your resume, saving on expensive API calls.
  - **Gemini-Powered Analysis**:
      - **Resume Parsing**: Understands your LaTeX resume to create a clean text summary for matching.
      - **Job Ranking**: Deeply analyzes and ranks the most promising jobs against your professional summary.
      - **Content Tailoring**: Subtly rephrases and reorders content in your LaTeX resume to align with each top-ranked job description.
  - **Automated PDF Generation**: Compiles the tailored LaTeX source into a polished PDF document.
  - **Email Notifications**: Sends a summary email with all generated resume PDFs attached.
  - **CI/CD Automation**: Includes a GitHub Actions workflow to run the job search on a schedule (e.g., daily).

## 📊 Workflow

1. Scrape Jobs
2. Filter out Processed Jobs
3. Filter by Salary and experience keywords
4. Filter by Cosine Similarity (Top 20)
5. Rank Jobs with Gemini (Top 10)
6. For each Top Job:
   - Generate Tailored LaTeX with Gemini
   - Compile to PDF
7. Send Summary Email with tailored resume PDFs
8. Update Processed Jobs Tracker

-----

## 🚀 Getting Started

Follow these steps to set up and run the assistant.

### 1\. Prerequisites

  - **Python 3.12+**: Ensure you have a modern version of Python installed.
  - **A LaTeX Distribution**: The script uses `pdflatex` to compile `.tex` files into PDFs. Make sure you have a distribution like [MiKTeX](https://miktex.org/) (Windows), [MacTeX](https://www.tug.org/mactex/) (macOS), or `texlive` (Linux) installed and available in your system's PATH.
  - **uv (Optional but Recommended)**: This project uses `uv` for package management. You can install it with `pip install uv`.

### 2\. Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/ai-job-assistant.git
    cd ai-job-assistant
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    # Create the virtual environment
    uv venv

    # Install dependencies from the lock file
    uv sync

    # OR
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a file named `.env` in the root directory by copying the example. Then, fill in your credentials.

    ```ini
    # .env

    # --- Gemini API Key ---
    # Get yours from Google AI Studio: https://makersuite.google.com/app/apikey
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

    # --- Email Notification Settings ---
    EMAIL_SMTP_HOST="smtp.gmail.com"  # Example for Gmail
    EMAIL_SMTP_PORT="587"
    EMAIL_SENDER_ADDRESS="your_email@gmail.com"
    # IMPORTANT: Use an App Password for security, not your regular password.
    # https://support.google.com/accounts/answer/185833
    EMAIL_SENDER_PASSWORD="your_google_app_password"
    EMAIL_TO="recipient_email@example.com"

    # --- (Optional) Zyte Proxy for Scraping ---
    # Not really required, but if your IP gets blocked, you might need a proxy
    # Set USE_PROXIES_IN_WORKFLOW=True in config.py to enable.
    ZYTE_API_KEY="YOUR_ZYTE_API_KEY"
    ```

4.  **Add Your Resume:**
    Place your resume in the root directory and name it `source_resume.tex`. The assistant will use this as the template for all modifications.

### 3\. Running the Assistant

Once configured, you can run the entire pipeline with a single command:

```bash
uv run python main.py
# OR
python main.py
```

The script will print its progress to the console. Generated resumes will be placed in the `generated_resumes/` directory, and if email is configured, you will receive a notification.

-----

## ⚙️ Configuration

The primary configuration file is `config.py`. Open it to tailor the job search to your specific needs.

| Parameter                 | Description                                                                 |
| ------------------------- | --------------------------------------------------------------------------- |
| `SEARCH_TERMS`            | A list of job titles to search for.                                         |
| `LOCATIONS`               | A list of locations. Use "Remote" for remote-only roles.                    |
| `MIN_SALARY_INR`          | The minimum annual salary (in INR) to consider. Set to 0 to disable.        |
| `MIN_EXPERIENCE_YEARS`    | Your minimum years of experience.                                           |
| `MAX_EXPERIENCE_YEARS`    | Your maximum years of experience.                                           |
| `JOB_SITES`               | A list of sites to scrape (e.g., "linkedin", "indeed", "naukri").           |
| `RESULTS_WANTED`          | The number of results to fetch per search term/location combination.        |
| `COSINE_FILTER_TOP_N`     | The number of jobs to keep after the initial cosine similarity filtering.     |
| `GEMINI_TOP_N`            | The number of top-ranked jobs for which to generate tailored resumes.       |
| `DELIVERY_METHOD`         | How to deliver results. Set to `"email"` or `"none"`.                         |
| `SOURCE_RESUME_PATH`      | The path to your master LaTeX resume file.                                  |
| `OUTPUT_DIR`              | The directory where generated resumes and temporary files will be stored.     |

## Automating with github actions

This repository includes a pre-configured GitHub Actions workflow in `.github/workflows/ai-job-assistant.yml`.

To enable it:

1.  **Fork this repository.**
2.  Go to your new repository's **Settings \> Secrets and variables \> Actions**.
3.  Add the same keys from your `.env` file (e.g., `GEMINI_API_KEY`, `EMAIL_SENDER_PASSWORD`) as repository secrets.
4.  The workflow is configured to run on a schedule (e.g., every day at 10:00 IST). You can adjust the `cron` schedule in the `.yml` file.

-----

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.