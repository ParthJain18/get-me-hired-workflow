import os
import subprocess
from config import OUTPUT_DIR
from PyPDF2 import PdfReader


def get_pdf_page_count(pdf_path):
    """Returns the number of pages in a PDF file."""
    if not pdf_path or not os.path.exists(pdf_path):
        return 0
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            return len(reader.pages)
    except Exception as e:
        print(f"⚠️ Could not read PDF page count for {pdf_path}: {e}")
        return 0
    

def create_resume_pdf(modified_latex_content, job):
    """
    Saves the modified LaTeX content and compiles it into a PDF.
    Returns the path to the generated PDF on success, otherwise None.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    company_name = str(job.get('company', 'UnknownCompany')).replace(' ', '_').replace('/', '_')
    job_title = str(job.get('title', 'UnknownTitle')).replace(' ', '_').replace('/', '_')
    base_filename = f"Resume_{company_name}_{job_title[:30]}"
    tex_filepath = os.path.join(OUTPUT_DIR, f"{base_filename}.tex")
    pdf_filepath = os.path.join(OUTPUT_DIR, f"{base_filename}.pdf")

    print(f"📄 Compiling PDF: {base_filename}.pdf")
    with open(tex_filepath, 'w', encoding='utf-8') as f:
        f.write(modified_latex_content)

    try:
        result = subprocess.run(
            [
                'pdflatex',
                '-interaction=nonstopmode',
                '-halt-on-error',
                '-output-directory', OUTPUT_DIR,
                tex_filepath
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        print(f"✅ Successfully created: {base_filename}.pdf")
        
        for ext in ['.aux', '.log', '.out']:
            aux_file = os.path.join(OUTPUT_DIR, f"{base_filename}{ext}")
            if os.path.exists(aux_file):
                os.remove(aux_file)
        return pdf_filepath
    except FileNotFoundError:
        print("❌ 'pdflatex' not found. Ensure a LaTeX distribution is installed and in your PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to compile {tex_filepath}. Error: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"❌ Compilation timed out for {tex_filepath}.")
        return None

# if(__name__ == "__main__"):
#     with open("./source_resume.tex", 'r', encoding='utf-8') as f:
#         sample_latex = f.read()
#     create_resume_pdf(sample_latex, {'company': 'TestCompany', 'title': 'TestTitle'})