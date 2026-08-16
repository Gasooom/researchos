from tests.e2e.test_research_api import build_e2e_client


def test_workspace_api_returns_research_and_evaluation() -> None:
    client, _ = build_e2e_client()

    response = client.post(
        "/workspace",
        params={
            "question": "How do evidence-grounded systems improve reliability?",
            "max_sources": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["result"]["question"]
        == "How do evidence-grounded systems improve reliability?"
    )

    assert body["execution"]["status"] == "success"
    assert isinstance(body["agents"], list)
    assert body["evaluation"]["overall_score"] >= 0.0
    assert body["evaluation"]["metrics"]
