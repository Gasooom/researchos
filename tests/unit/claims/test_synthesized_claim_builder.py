from datetime import UTC, datetime

import pytest

from app.application.claims.support_validator import ClaimSupportValidator
from app.application.claims.synthesizer import SynthesizedClaimBuilder
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Claim, Evidence, Source
from app.domain.research.multi_agent import MultiAgentResearchResult
from app.domain.research.synthesis import SynthesisResult

EXCERPT = (
    "Retrieval latency rose sharply once the index exceeded ten million "
    "vectors, according to the published load tests."
)


def make_evidence(excerpt: str = EXCERPT, relevance: float = 0.94) -> Evidence:
    return Evidence(
        source=Source(
            title="Vector Index Load Tests",
            url="https://example.com/load-tests",
            publisher="Example Research",
            retrieved_at=datetime.now(UTC),
        ),
        excerpt=excerpt,
        relevance=relevance,
    )


def make_result(
    supporting_points: list[str],
    evidence: list[Evidence] | None = None,
) -> MultiAgentResearchResult:
    return MultiAgentResearchResult(
        evidence=evidence or [make_evidence()],
        analysis=AnalysisResult(
            summary="Analysis summary.",
            key_points=["A key point."],
            confidence=0.9,
        ),
        synthesis=SynthesisResult(
            answer="A synthesized answer.",
            supporting_points=supporting_points,
            confidence=0.9,
        ),
    )


def test_claim_statement_is_not_the_evidence_excerpt() -> None:
    """The defect M6 fixes: statements used to be copies of their evidence."""
    finding = "Indexes above ten million vectors degrade retrieval latency."

    claims = SynthesizedClaimBuilder().build([make_result([finding])])

    assert len(claims) == 1
    assert claims[0].statement == finding
    assert claims[0].statement != claims[0].evidence[0].excerpt


def test_evidence_excerpt_is_preserved_verbatim() -> None:
    claims = SynthesizedClaimBuilder().build(
        [make_result(["A synthesized finding."])],
    )

    assert claims[0].evidence[0].excerpt == EXCERPT
    assert claims[0].evidence[0].relevance == 0.94
    assert str(claims[0].evidence[0].source.url) == "https://example.com/load-tests"


def test_validator_receives_independent_claim_and_evidence_text() -> None:
    """Overlap is now computed between two independently worded texts."""
    finding = "Indexes above ten million vectors degrade retrieval latency."

    claims = SynthesizedClaimBuilder().build([make_result([finding])])

    verification = ClaimSupportValidator().verify(claims[0])

    assert 0.0 < verification.best_overlap < 1.0


def test_unrelated_finding_is_reported_as_unsupported() -> None:
    """The metric can now discriminate: unrelated wording fails validation."""
    finding = "Quarterly revenue in the Latin American segment declined."

    claims = SynthesizedClaimBuilder().build([make_result([finding])])

    verification = ClaimSupportValidator().verify(claims[0])

    assert verification.status.value in {"weak", "unsupported"}
    assert ClaimSupportValidator().is_supported(claims[0]) is False


def test_well_grounded_finding_remains_supported() -> None:
    finding = (
        "Retrieval latency rose sharply once the index exceeded ten million "
        "vectors according to published load tests."
    )

    claims = SynthesizedClaimBuilder().build([make_result([finding])])

    assert ClaimSupportValidator().is_supported(claims[0]) is True


def test_every_supporting_point_becomes_its_own_claim() -> None:
    claims = SynthesizedClaimBuilder().build(
        [make_result(["First finding.", "Second finding.", "Third finding."])],
    )

    assert [claim.statement for claim in claims] == [
        "First finding.",
        "Second finding.",
        "Third finding.",
    ]


def test_blank_supporting_points_are_skipped() -> None:
    claims = SynthesizedClaimBuilder().build(
        [make_result(["A real finding.", "   "])],
    )

    assert len(claims) == 1
    assert claims[0].statement == "A real finding."


def test_claims_carry_all_evidence_from_their_agent_result() -> None:
    evidence = [
        make_evidence("First excerpt about latency.", 0.9),
        make_evidence("Second excerpt about indexing.", 0.8),
    ]

    claims = SynthesizedClaimBuilder().build(
        [make_result(["A finding."], evidence=evidence)],
    )

    assert len(claims[0].evidence) == 2


def test_builder_accepts_an_injected_grounder() -> None:
    """Claim construction stays testable through dependency injection."""

    class RecordingGrounder:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def ground(self, statement: str, evidence: list[Evidence]) -> Claim:
            self.calls.append(statement)

            return Claim(statement=statement, evidence=evidence)

    grounder = RecordingGrounder()

    SynthesizedClaimBuilder(grounder=grounder).build(
        [make_result(["Injected finding."])],
    )

    assert grounder.calls == ["Injected finding."]


def test_empty_result_list_produces_no_claims() -> None:
    assert SynthesizedClaimBuilder().build([]) == []


def test_grounder_still_rejects_evidence_free_findings() -> None:
    result = make_result(["A finding."])
    result.evidence.clear()

    with pytest.raises(ValueError, match="evidence must not be empty"):
        SynthesizedClaimBuilder().build([result])
