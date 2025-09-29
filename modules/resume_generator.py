import os
import subprocess
from typing import Dict, List, Optional, Tuple

from config import OUTPUT_DIR
from PyPDF2 import PdfReader


TAILORED_SECTION_START = "% === TAILORED_CONTENT_START ==="
TAILORED_SECTION_END = "% === TAILORED_CONTENT_END ==="

DEFAULT_SUMMARY_BULLETS = [
    "Enthusiastic software engineer combining AI/ML research experience with production-grade backend development.",
    "Proven ability to ship data-intensive solutions, collaborate with cross-functional teams, and adapt quickly to new stacks.",
    "Passionate about leveraging GenAI, Python, and cloud-native tooling to deliver measurable impact."
]

DEFAULT_KEYWORDS = [
    "Python | FastAPI | LangChain | AWS | LLM Ops",
    "Machine Learning | NLP | Computer Vision | Data Pipelines",
    "Kotlin | Jetpack Compose | React | MongoDB"
]

DEFAULT_HIGHLIGHT_BULLETS = [
    "Delivered AI-powered tooling, analytics dashboards, and cross-platform apps across internships and hackathons.",
    "Emphasized measurable outcomes: 200% data expansion, hundreds of active users, and published research output.",
    "Comfortable adapting project deliverables to stakeholder needs under tight deadlines."
]


def _escape_latex(text: str) -> str:
    if not text:
        return ""

    replacements = [
        ("&", r"\\&"),
        ("%", r"\\%"),
        ("$", r"\\$"),
        ("#", r"\\#"),
        ("_", r"\\_"),
        ("{", r"\\{"),
        ("}", r"\\}"),
        ("~", r"\\textasciitilde{}"),
        ("^", r"\\textasciicircum{}"),
    ]

    placeholder = "\uFFFF"
    escaped = text.replace("\\", placeholder)
    for old, new in replacements:
        escaped = escaped.replace(old, new)
    escaped = escaped.replace(placeholder, r"\\textbackslash{}")
    return escaped.strip()


def _normalise_items(items: Optional[List[str]], fallback: List[str], limit: int) -> Tuple[List[str], bool]:
    if not items:
        return [_escape_latex(item) for item in fallback[:limit]], False

    cleaned: List[str] = []
    seen = set()
    for entry in items:
        if not entry:
            continue
        escaped = _escape_latex(entry)
        key = escaped.lower()
        if not escaped or key in seen:
            continue
        cleaned.append(escaped)
        seen.add(key)
        if len(cleaned) >= limit:
            break

    if not cleaned:
        return [_escape_latex(item) for item in fallback[:limit]], False

    return cleaned, True


def _build_itemize_block(items: List[str]) -> str:
    if not items:
        return "    \\item (content unavailable)"
    return "\n".join(f"    \\item {item}" for item in items)


def _build_tailored_block(content: Dict[str, List[str]], job: Dict) -> Tuple[str, bool]:
    summary_bullets, summary_used = _normalise_items(content.get(
        'summary_bullets') if content else None, DEFAULT_SUMMARY_BULLETS, 3)
    keywords, keywords_used = _normalise_items(content.get(
        'keywords') if content else None, DEFAULT_KEYWORDS, 8)
    highlight_bullets, highlights_used = _normalise_items(content.get(
        'highlight_bullets') if content else None, DEFAULT_HIGHLIGHT_BULLETS, 3)

    ai_content_used = summary_used or keywords_used or highlights_used

    block = f"""\\section{{Role Alignment Summary}}
\\begin{{itemize}}
{_build_itemize_block(summary_bullets)}
\\end{{itemize}}

\\section{{Target Keywords}}
\\begin{{itemize}}
{_build_itemize_block(keywords)}
\\end{{itemize}}

\\section{{Job-Specific Highlights}}
\\begin{{itemize}}
{_build_itemize_block(highlight_bullets)}
\\end{{itemize}}"""

    return block, ai_content_used


def _replace_tailored_block(latex_source: str, new_block: str) -> str:
    start_idx = latex_source.find(TAILORED_SECTION_START)
    end_idx = latex_source.find(TAILORED_SECTION_END)

    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        print("⚠️ Could not find tailored content markers in the resume template. Returning original content.")
        return latex_source

    start_idx += len(TAILORED_SECTION_START)
    before = latex_source[:start_idx]
    after = latex_source[end_idx:]

    return f"{before}\n{new_block.strip()}\n{after}"


def prepare_resume_latex(base_latex: str, job: Dict, tailored_content: Optional[Dict[str, List[str]]] = None) -> Tuple[str, bool]:
    """Injects tailored content into the resume template and returns the updated LaTeX along with a flag indicating whether AI content was used."""

    new_block, used_ai_content = _build_tailored_block(
        tailored_content or {}, job)
    updated_latex = _replace_tailored_block(base_latex, new_block)
    return updated_latex, used_ai_content


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

    company_name = str(job.get('company', 'UnknownCompany')
                       ).replace(' ', '_').replace('/', '_')
    job_title = str(job.get('title', 'UnknownTitle')
                    ).replace(' ', '_').replace('/', '_')
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
        if e.stdout:
            print(f"❌ LaTeX stdout for {tex_filepath}:\n{e.stdout}")
        if e.stderr:
            print(f"❌ LaTeX stderr for {tex_filepath}:\n{e.stderr}")
        else:
            print(
                f"❌ Failed to compile {tex_filepath}. No stderr output was produced.")
        return None
    except subprocess.TimeoutExpired:
        print(f"❌ Compilation timed out for {tex_filepath}.")
        return None

# if(__name__ == "__main__"):
#     with open("./source_resume.tex", 'r', encoding='utf-8') as f:
#         sample_latex = f.read()
#     create_resume_pdf(sample_latex, {'company': 'TestCompany', 'title': 'TestTitle'})
