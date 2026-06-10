from pathlib import Path


APPROVAL_ENDPOINT = "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/decision"


def _approval_action_source() -> str:
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function getAgenticApprovalRequestId")
    end = source.index("function renderAgenticReviewData")
    return source[start:end]


def test_approval_ui_action_calls_only_approval_decision_endpoint():
    source = _approval_action_source()

    assert APPROVAL_ENDPOINT in source
    assert "fetchJson(" in source
    assert "reviewer_id: reviewerId" in source
    assert "review_decision: reviewDecision" in source
    assert "review_reason:" in source
    assert "decided_at:" in source
    assert "/application-actions" not in source


def test_approval_ui_action_keeps_unsafe_paths_out_of_action_snippet():
    source = _approval_action_source()

    forbidden_call_tokens = [
        "application-actions",
        "queue mutation",
        "executeLive",
        "run_application_planning",
        "application_submission",
        "scheduler/background",
        "submit application",
        "mutation execution",
    ]

    for token in forbidden_call_tokens:
        assert token not in source


def test_approval_ui_action_blocks_when_required_identity_or_request_id_missing():
    source = _approval_action_source()

    assert "function getAgenticApprovalRequestId" in source
    assert "function getAgenticApprovalReviewerId" in source
    assert "reviewer identity unavailable" in source
    assert "approval_request_id unavailable" in source
    assert "Approval action blocked:" in source
    assert "disabledAttr" in source
    assert "data-agentic-approval-decision" in source


def test_approval_ui_action_response_handling_does_not_trigger_follow_up_execution():
    source = _approval_action_source()

    assert "Execution remains disabled." in source
    assert "window.location" not in source
    assert "refreshAgenticReviewFeedbackSummary" not in source
    assert "recordAgenticReviewFeedback" not in source
