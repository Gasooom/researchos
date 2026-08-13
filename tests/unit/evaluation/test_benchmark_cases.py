from app.application.evaluation.benchmark_cases import (
    get_benchmark_cases,
)


def test_benchmark_dataset_is_non_empty() -> None:
    cases = get_benchmark_cases()

    assert cases


def test_benchmark_case_ids_are_unique() -> None:
    cases = get_benchmark_cases()

    ids = [case.id for case in cases]

    assert len(ids) == len(set(ids))


def test_benchmark_cases_have_expected_focus() -> None:
    cases = get_benchmark_cases()

    for case in cases:
        assert case.question
        assert case.expected_focus


def test_benchmark_dataset_is_reproducible() -> None:
    first = get_benchmark_cases()
    second = get_benchmark_cases()

    assert first == second
