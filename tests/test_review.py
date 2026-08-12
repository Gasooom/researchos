from app.core.models.review import ReviewDecision, ReviewStatus


def test_review_status_values() -> None:
    assert ReviewStatus.NOT_REQUIRED.value == "not_required"
    assert ReviewStatus.PENDING.value == "pending"
    assert ReviewStatus.APPROVED.value == "approved"
    assert ReviewStatus.REJECTED.value == "rejected"


def test_review_decision_values() -> None:
    assert ReviewDecision.APPROVE.value == "approve"
    assert ReviewDecision.REJECT.value == "reject"
    assert ReviewDecision.REQUEST_MORE_EVIDENCE.value == ("request_more_evidence")
