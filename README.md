# AI-Powered Job Application Assistant

This project automates the job search process by scraping job sites, using NLP to find the best matches, leveraging the Gemini API to rank and tailor content, and automatically generating custom LaTeX resumes.

## Features
- Scrapes multiple job sites (LinkedIn, Indeed) via JobSpy.
- Uses Cosine Similarity for efficient, low-cost pre-filtering.
- Leverages the Gemini API for intelligent final ranking and resume content generation.
- Automatically compiles tailored resumes into PDFs.
- Highly configurable via `config.py`.

## Project Structure
The project is modular, with different tasks handled by separate files in the `/modules` directory. `main.py` orchestrates the entire workflow.

---

## ?? Local Setup & Execution

**1. Prerequisites:**
   - Python 3.9+
   - A LaTeX distribution (like [MiKTeX](https://miktex.org/download) for Windows, or [TeX Live](https://www.tug.org/texlive/) for Mac/Linux) to compile `.tex` files.

**2. Clone the Repository:**
   ```bash
   git clone <your-repo-url>
   cd heroku-job-assistant
   ```

**3. Set up a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

**4. Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

**5. Create Essential Files:**
   - **`.env`**: Create this file in the root directory and add your API key:
     ```
     GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
     ```
   - **`master_resume.txt`**: Create this file and paste the full text of your resume into it.
   - **`resume_template.tex`**: Create your LaTeX resume template with the placeholders `%%GEMINI_CUSTOM_SUMMARY%%` and `%%GEMINI_POWER_KEYWORDS%%`.

**6. Configure Your Search:**
   - Open `config.py` and modify the search terms, locations, and other settings to match your needs.

**7. Run the Script:**
   ```bash
   python main.py
   ```
   Your generated resumes will appear in the `/generated_resumes` folder.

---

## ?? Heroku Deployment

**1. Login to Heroku & Create App:**
   ```bash
   heroku login
   heroku create your-app-name-here --buildpack heroku/python
   heroku buildpacks:add --index 1 microsoft/playwright-node -a your-app-name-here
   ```

**2. Set Config Vars:**
   - Your Gemini API key must be set as an environment variable on Heroku.
   ```bash
   heroku config:set GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE" -a your-app-name-here
   ```

**3. Deploy the Code:**
   - Make sure all your files are committed to git.
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push heroku main
   ```

**4. Add & Configure Scheduler:**
   - Provision the free scheduler add-on.
   ```bash
   heroku addons:create scheduler:standard -a your-app-name-here
   ```
   - Open the scheduler dashboard.
   ```bash
   heroku addons:open scheduler -a your-app-name-here
   ```
   - Create a new job that runs **daily** with the command: `python main.py`.
