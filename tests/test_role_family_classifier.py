from src.intelligence.role_family_classifier import classify_role_family, classify_roles


def test_it_wide_role_family_classifier_uses_strong_title_signals():
    cases = [
        ("Backend Engineer", "backend_engineering"),
        ("Frontend Engineer", "frontend_engineering"),
        ("Full Stack Engineer", "fullstack_engineering"),
        ("Software Engineer", "software_engineering"),
        ("DevOps Engineer", "cloud_devops"),
        ("Site Reliability Engineer", "sre"),
        ("QA Automation Engineer", "qa_automation"),
        ("Security Engineer", "security"),
        ("Data Scientist", "data_science"),
        ("Data Engineer", "data_engineering"),
        ("ML Engineer", "ml_ai_engineering"),
    ]

    for title, expected_role_family in cases:
        assert classify_role_family({"title": title}) == expected_role_family


def test_role_family_classifier_returns_other_for_unknown_non_tech_role():
    assert classify_role_family({"title": "Account Executive"}) == "other"


def test_role_family_classifier_prefers_specific_titles_before_broad_software():
    assert classify_role_family({"title": "Fullstack Software Engineer"}) == "fullstack_engineering"
    assert classify_role_family({"title": "Backend Software Engineer"}) == "backend_engineering"
    assert classify_role_family({"title": "Frontend Software Engineer"}) == "frontend_engineering"
    assert classify_role_family({"title": "Machine Learning Engineer"}) == "ml_ai_engineering"


def test_role_family_classifier_uses_skill_tool_fallback_after_title_signals():
    assert classify_role_family({"title": "", "required_skills": ["test automation"]}) == "qa_automation"
    assert classify_role_family({"title": "", "required_skills": ["threat modeling"]}) == "security"
    assert classify_role_family({"title": "", "required_skills": ["data pipeline"]}) == "data_engineering"
    assert classify_role_family({"title": "", "required_skills": ["pytorch"]}) == "ml_ai_engineering"


def test_classify_roles_mutates_jobs_with_role_family():
    jobs = [
        {"title": "Backend Engineer"},
        {"title": "Account Executive"},
    ]

    returned = classify_roles(jobs)

    assert returned is jobs
    assert jobs[0]["role_family"] == "backend_engineering"
    assert jobs[1]["role_family"] == "other"
