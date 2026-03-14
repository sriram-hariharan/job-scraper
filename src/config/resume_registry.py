"""
Resume Registry

Maps job role families → candidate resumes.

This prevents the matcher from comparing a job against
irrelevant resumes (ex: Data Engineer resume for Analyst job).

All filenames must match the files inside RESUME_DIR.
"""

RESUME_REGISTRY = {

    # ---------------------------
    # Data Analyst roles
    # ---------------------------
    "data analyst": [
        "Sriram_Neelakantan_Data_Analyst.pdf"
    ],

    # ---------------------------
    # Core Data Scientist roles
    # ---------------------------
    "data scientist": [
        "Sriram_Neelakantan_Data_Scientist.pdf",
        "Sriram_Neelakantan_General_Data_Scientist.pdf",
        "Sriram_Neelakantan_Product_Data_Scientist.pdf",
        "Sriram_Neelakantan_Healthcare_Data_Scientist.pdf",
        "Sriram_Neelakantan_Quantitative_Data_Scientist.pdf",
        "Sriram_Neelakantan_Senior_Data_Scientist.pdf",
        "Sriram_Neelakantan_Data_Scientist_Analytics.pdf"
    ],

    # ---------------------------
    # Applied Scientist roles
    # ---------------------------
    "applied scientist": [
        "Sriram_Neelakantan_Applied_Scientist.pdf"
    ],

    # ---------------------------
    # AI / GenAI Engineer roles
    # ---------------------------
    "ai engineer": [
        "Sriram_Neelakantan_AI1.pdf",
        "Sriram_Neelakantan_AI2.pdf"
    ],

    # ---------------------------
    # ML Engineer roles
    # ---------------------------
    "machine learning engineer": [
        "Sriram_Neelakantan_AI1.pdf",
        "Sriram_Neelakantan_AI2.pdf"
    ],

    # ---------------------------
    # Data Engineer roles
    # ---------------------------
    "data engineer": [
        "Sriram_Hariharan_Data_Engineer.pdf"
    ]
}


def get_candidate_resumes(role_family: str):
    """
    Return resumes eligible for a given role family.
    """

    role_family = (role_family or "").lower()

    if role_family in RESUME_REGISTRY:
        return RESUME_REGISTRY[role_family]

    # fallback: allow all resumes if role unknown
    all_resumes = []
    for resumes in RESUME_REGISTRY.values():
        all_resumes.extend(resumes)

    return list(set(all_resumes))