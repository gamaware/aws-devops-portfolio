import pytest

from portfolio_check import live
from portfolio_check.model import parse

TOPICS = ("terraform", "lab", "portfolio", "devops", "aws")


def _live(**overrides):
    payload = {
        "description": "Demonstrates a rescue through a report; verified offline with tests.",
        "visibility": "PUBLIC",
        "usesCustomOpenGraphImage": True,
        "repositoryTopics": {"nodes": [{"topic": {"name": t}} for t in TOPICS]},
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def repo(raw):
    return parse(raw).services[0].repo


def test_matching_repository_passes(repo):
    assert [r.status for r in live.compare(repo, _live())] == ["pass"] * 4


def test_missing_repository_fails(repo):
    assert [(r.status, r.message) for r in live.compare(repo, None)] == [("FAIL", "example-lab: not found on GitHub")]


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"visibility": "PRIVATE"}, "PRIVATE"),
        ({"description": "Something else."}, "description matches"),
        ({"repositoryTopics": {"nodes": []}}, "topics match"),
        ({"usesCustomOpenGraphImage": False}, "social preview"),
    ],
)
def test_each_difference_fails(repo, overrides, fragment):
    failed = [r.message for r in live.compare(repo, _live(**overrides)) if r.status == "FAIL"]
    assert len(failed) == 1
    assert fragment in failed[0]


def test_extra_repository_checks_visibility_only(raw):
    raw["more"] = [{"repo": {**raw["services"][0]["repo"], "standard": False}, "summary": "Extra."}]
    repo = parse(raw).more[0].repo
    results = live.compare(repo, _live(description="Old text.", usesCustomOpenGraphImage=False))
    assert [r.status for r in results] == ["pass", "skip"]


def test_run_needs_a_token(raw, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        live.run(parse(raw))
