from src.agents.context import JobApplicationContext, job_application_context_payload


def test_job_application_context_can_be_created_and_serialized():
    context = JobApplicationContext(
        context_id="ctx_1",
        owner_user_id="user_1",
        run_id="run_1",
        job={"company": "Acme", "title": "Backend Engineer"},
        prefilter={"passed": True},
        trace=[{"agent_step_id": "step_1"}],
    )

    payload = context.to_dict()

    assert payload["context_id"] == "ctx_1"
    assert payload["owner_user_id"] == "user_1"
    assert payload["run_id"] == "run_1"
    assert payload["job"]["company"] == "Acme"
    assert payload["prefilter"]["passed"] is True
    assert payload["jd_intelligence"] == {}
    assert payload["trace"] == [{"agent_step_id": "step_1"}]


def test_job_application_context_round_trips_from_dict():
    payload = job_application_context_payload(
        context_id="ctx_2",
        owner_user_id="user_2",
        run_id="run_2",
        resume_match={"resume": "resume.pdf"},
        strategy={"action": "review"},
    )

    restored = JobApplicationContext.from_dict(payload)

    assert restored.to_dict() == payload
