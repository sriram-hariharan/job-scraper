import os
from pathlib import Path
from typing import List, Dict
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

load_dotenv()

RESUME_DIR = os.getenv("RESUME_DIR")

if not RESUME_DIR:
    raise RuntimeError("RESUME_DIR not set in environment")

RESUME_DIR = Path(RESUME_DIR)


def normalize_text(text: str) -> str:
    """
    Clean resume text for embedding / analysis.
    """
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text


def extract_resume_text(pdf_path: Path) -> str:
    """
    Extract text from a resume PDF.
    """
    try:
        text = extract_text(str(pdf_path))
        return normalize_text(text)
    except Exception as e:
        print(f"Failed to parse resume {pdf_path}: {e}")
        return ""


def load_resumes() -> List[Dict]:
    """
    Load all resumes from RESUME_DIR.

    Returns:
    [
        {
            "resume_name": "...pdf",
            "path": "...",
            "text": "resume text..."
        }
    ]
    """

    resumes = []

    if not RESUME_DIR.exists():
        raise RuntimeError(f"Resume directory not found: {RESUME_DIR}")

    for file in RESUME_DIR.iterdir():

        if file.suffix.lower() != ".pdf":
            continue

        text = extract_resume_text(file)

        if not text:
            continue

        resumes.append(
            {
                "resume_name": file.name,
                "path": str(file),
                "text": text,
            }
        )

    return resumes


def load_resumes_by_name(names: List[str]) -> List[Dict]:
    """
    Load only specific resumes by filename.

    Used by resume matcher when filtering by role family.
    """

    resumes = []

    for name in names:

        path = RESUME_DIR / name

        if not path.exists():
            print(f"Resume missing: {name}")
            continue

        text = extract_resume_text(path)

        if not text:
            continue

        resumes.append(
            {
                "resume_name": name,
                "path": str(path),
                "text": text,
            }
        )

    return resumes