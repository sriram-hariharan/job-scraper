import os
import re
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
    Clean resume text for embedding / broad analysis.
    Keeps semantic content but removes layout/newline structure.
    """
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text.strip()


def normalize_raw_layout_text(text: str) -> str:
    """
    Light cleanup that preserves line structure for section parsing.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_resume_texts(pdf_path: Path) -> Dict[str, str]:
    """
    Extract both raw-layout text and normalized flat text from a resume PDF.
    """
    try:
        raw_text = extract_text(str(pdf_path))
        raw_text = normalize_raw_layout_text(raw_text)
        normalized_text = normalize_text(raw_text)

        return {
            "raw_text": raw_text,
            "text": normalized_text,
        }
    except Exception as e:
        print(f"Failed to parse resume {pdf_path}: {e}")
        return {
            "raw_text": "",
            "text": "",
        }


def load_resumes() -> List[Dict]:
    resumes = []

    if not RESUME_DIR.exists():
        raise RuntimeError(f"Resume directory not found: {RESUME_DIR}")

    for file in RESUME_DIR.iterdir():
        if file.suffix.lower() != ".pdf":
            continue

        extracted = extract_resume_texts(file)

        if not extracted["raw_text"]:
            continue

        resumes.append(
            {
                "resume_name": file.name,
                "path": str(file),
                "raw_text": extracted["raw_text"],
                "text": extracted["text"],
            }
        )

    return resumes


def load_resumes_by_name(names: List[str]) -> List[Dict]:
    resumes = []

    for name in names:
        path = RESUME_DIR / name

        if not path.exists():
            print(f"Resume missing: {name}")
            continue

        extracted = extract_resume_texts(path)

        if not extracted["raw_text"]:
            continue

        resumes.append(
            {
                "resume_name": name,
                "path": str(path),
                "raw_text": extracted["raw_text"],
                "text": extracted["text"],
            }
        )

    return resumes