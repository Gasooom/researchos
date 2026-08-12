from datetime import UTC, datetime

import pytest

from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
    SupportLevel,
)
from app.domain.research.models import Claim, Evidence, Source


def make_evidence(relevance: float) -> Evidence:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/reliability",
        publisher="example.com",
        retrieved_at=datetime(
            2026,
            8,
            12,
            7,
            0,
            tzinfo=UTC,
        ),
    )

    return Evidence(
        source=source,
        excerpt="AI agents can fail unpredictably during multi-step tasks.",
        relevance=relevance,
    )


def make_claim(*relevances: float) -> Claim:
    return Claim(
        statement="AI agents can fail unpredictably during multi-step tasks.",
        evidence=[make_evidence(relevance) for relevance in relevances],
    )


def test_classifier_returns_supported() -> None:
    classifier = ClaimSupportClassifier(
        supported_threshold=0.8,
        weak_threshold=0.5,
    )

    assert classifier.classify(make_claim(0.92)) == SupportLevel.SUPPORTED


def test_classifier_returns_weak() -> None:
    classifier = ClaimSupportClassifier(
        supported_threshold=0.8,
        weak_threshold=0.5,
    )

    assert classifier.classify(make_claim(0.63)) == SupportLevel.WEAK


def test_classifier_returns_unsupported() -> None:
    classifier = ClaimSupportClassifier(
        supported_threshold=0.8,
        weak_threshold=0.5,
    )

    assert classifier.classify(make_claim(0.31)) == SupportLevel.UNSUPPORTED


def test_classifier_uses_strongest_evidence() -> None:
    classifier = ClaimSupportClassifier(
        supported_threshold=0.8,
        weak_threshold=0.5,
    )

    claim = make_claim(0.32, 0.41, 0.88)

    assert classifier.classify(claim) == SupportLevel.SUPPORTED


def test_classifier_rejects_invalid_thresholds() -> None:
    with pytest.raises(ValueError, match="weak_threshold"):
        ClaimSupportClassifier(
            supported_threshold=0.4,
            weak_threshold=0.6,
        )

    with pytest.raises(ValueError, match="between 0 and 1"):
        ClaimSupportClassifier(
            supported_threshold=1.2,
            weak_threshold=0.5,
        )
