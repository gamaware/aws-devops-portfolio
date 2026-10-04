import shutil

import pytest

from conftest import INDEX_ROOT, STANDARD_README, make_repo
from portfolio_check import checks
from portfolio_check.covers import card_image
from portfolio_check.model import load, parse


def _statuses(results, fragment):
    return [r.status for r in results if fragment in r.message]


@pytest.fixture
def workspace(tmp_path, raw):
    """An index with one card cover and one sibling repository that passes everything."""
    index = tmp_path / "index"
    (index / "assets").mkdir(parents=True)
    repo = make_repo(tmp_path / "example-lab-folder")
    card_image(repo / "docs/assets/cover.png").save(index / "assets/audit.png")
    return parse(raw), index, tmp_path, repo


def test_compliant_repository_passes(workspace):
    catalog, index, root, _ = workspace
    results = checks.cover_results(catalog, index, root) + checks._repo_results(
        catalog, catalog.services[0].repo, root, catalog.services[0]
    )
    assert [r for r in results if r.status != "pass"] == []


def test_missing_folder_fails(workspace):
    catalog, _, root, repo = workspace
    shutil.rmtree(repo)
    results = checks._repo_results(catalog, catalog.services[0].repo, root, catalog.services[0])
    assert results[0].status == "FAIL"
    assert "clone it there or set REPOS_ROOT" in results[0].message


@pytest.mark.parametrize("missing", ["LICENSE", "CHANGELOG.md", "docs/assets/cover.png"])
def test_missing_required_file_fails(workspace, missing):
    catalog, _, root, repo = workspace
    (repo / missing).unlink()
    results = checks._repo_results(catalog, catalog.services[0].repo, root, catalog.services[0])
    assert _statuses(results, f"missing {missing}") == ["FAIL"]


def test_too_few_adrs_fail(workspace):
    catalog, _, root, repo = workspace
    (repo / "docs/adr/0002-decision.md").unlink()
    results = checks._repo_results(catalog, catalog.services[0].repo, root, catalog.services[0])
    assert _statuses(results, "1 ADRs") == ["FAIL"]


def test_readme_order_missing_index_link_and_artifact_fail(workspace):
    catalog, _, root, repo = workspace
    text = STANDARD_README.replace("## Architecture\n\n", "").replace(
        "https://github.com/example-owner/example-index", ""
    )
    (repo / "README.md").write_text(text, encoding="utf-8")
    (repo / "report/REPORT.md").unlink()
    results = checks._repo_results(catalog, catalog.services[0].repo, root, catalog.services[0])
    assert _statuses(results, "missing sections: Architecture") == ["FAIL"]
    assert _statuses(results, "no link to") == ["FAIL"]
    assert _statuses(results, "artifact report/REPORT.md not found") == ["FAIL"]


def test_changed_cover_fails(workspace):
    catalog, index, root, repo = workspace
    shutil.copy(INDEX_ROOT / "assets/eks.png", repo / "docs/assets/cover.png")
    assert _statuses(checks.cover_results(catalog, index, root), "run make covers") == ["FAIL"]


def test_wrong_size_and_orphan_covers_fail(workspace):
    catalog, index, root, _ = workspace
    shutil.copy(INDEX_ROOT / "docs/assets/social-preview.png", index / "assets/audit.png")
    shutil.copy(INDEX_ROOT / "assets/eks.png", index / "assets/unused.png")
    results = checks.cover_results(catalog, index, root)
    assert _statuses(results, "expected PNG (640, 480)") == ["FAIL"]
    assert _statuses(results, "assets/unused.png belongs to no service") == ["FAIL"]


def test_in_progress_repository_skips_structure_and_missing_cover(workspace, raw):
    _, index, root, repo = workspace
    raw["services"][0]["repo"]["status"] = "in-progress"
    catalog = parse(raw)
    shutil.rmtree(repo / "docs")
    results = checks.cover_results(catalog, index, root) + checks._repo_results(
        catalog, catalog.services[0].repo, root, catalog.services[0]
    )
    assert [r.status for r in results] == ["skip", "pass", "skip"]


def test_in_progress_repository_may_be_absent(workspace, raw):
    _, _, root, repo = workspace
    raw["services"][0]["repo"]["status"] = "in-progress"
    catalog = parse(raw)
    shutil.rmtree(repo)
    results = checks._repo_results(catalog, catalog.services[0].repo, root, catalog.services[0])
    assert [r.status for r in results] == ["skip"]


def test_extra_repository_needs_only_readme_and_license(workspace, raw):
    raw["more"] = [{"repo": {**raw["services"][0]["repo"], "standard": False}, "summary": "Extra."}]
    raw["services"][0]["repo"] = {**raw["services"][0]["repo"], "name": "other", "local": "other"}
    catalog = parse(raw)
    _, _, root, repo = workspace
    (repo / "CHANGELOG.md").unlink()
    shutil.rmtree(repo / "docs")
    results = checks._repo_results(catalog, catalog.more[0].repo, root, None)
    assert [r.status for r in results] == ["pass", "pass"]


def test_png_size_rejects_non_png(tmp_path):
    path = tmp_path / "fake.png"
    path.write_bytes(b"GIF89a" + b"\0" * 30)
    assert checks.png_size(path) is None


def test_png_size_rejects_truncated_png(tmp_path):
    path = tmp_path / "truncated.png"
    path.write_bytes((INDEX_ROOT / "docs/assets/social-preview.png").read_bytes()[:4096])
    assert checks.png_size(path) is None


def test_unreadable_source_cover_fails_without_traceback(workspace):
    catalog, index, root, repo = workspace
    (repo / "docs/assets/cover.png").write_bytes(b"not an image")
    assert _statuses(checks.cover_results(catalog, index, root), "cannot compare") == ["FAIL"]


def test_missing_index_readme_is_reported(tmp_path):
    catalog = load(INDEX_ROOT / "data/catalog.yaml")
    results = checks.index_results(catalog, tmp_path)
    assert "FAIL" in _statuses(results, "BEGIN GENERATED")


def test_repository_passes_its_own_index_checks():
    catalog = load(INDEX_ROOT / "data/catalog.yaml")
    assert [r for r in checks.index_results(catalog, INDEX_ROOT) if r.status != "pass"] == []


def test_index_link_must_be_exact(workspace):
    catalog, _, root, repo = workspace
    text = STANDARD_README.replace("example-owner/example-index)", "example-owner/example-index-old)")
    (repo / "README.md").write_text(text, encoding="utf-8")
    results = checks._repo_results(catalog, catalog.services[0].repo, root, catalog.services[0])
    assert _statuses(results, "no link to") == ["FAIL"]


def test_cover_that_is_not_four_by_three_fails(workspace):
    catalog, index, root, repo = workspace
    shutil.copy(INDEX_ROOT / "docs/assets/social-preview.png", repo / "docs/assets/cover.png")
    assert _statuses(checks.cover_results(catalog, index, root), "expected a 4:3 image") == ["FAIL"]


def test_index_readme_with_stale_counts_fails(tmp_path):
    catalog = load(INDEX_ROOT / "data/catalog.yaml")
    shutil.copytree(INDEX_ROOT / "docs", tmp_path / "docs")
    for name in ("README.md", "LICENSE", "CHANGELOG.md"):
        shutil.copy(INDEX_ROOT / name, tmp_path / name)
    text = (tmp_path / "README.md").read_text(encoding="utf-8")
    (tmp_path / "README.md").write_text(text.replace("sixteen public", "fifteen public"), encoding="utf-8")
    assert _statuses(checks.index_results(catalog, tmp_path), "services backed by") == ["FAIL"]
