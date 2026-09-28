import pytest

from conftest import INDEX_ROOT
from portfolio_check.model import CatalogError, catalog_rule_errors, load, loads, parse, repo_rule_errors
from portfolio_check.render import anchor


def test_repository_catalog_passes_every_rule():
    catalog = load(INDEX_ROOT / "data/catalog.yaml")
    assert catalog_rule_errors(catalog) == []
    assert len(catalog.services) == 10


def test_minimal_catalog_parses_with_defaults(raw):
    catalog = parse(raw)
    service = catalog.services[0]
    assert service.repo.status == "ready"
    assert service.repo.standard is True
    assert catalog.artifact_url(service) == "https://github.com/example-owner/example-lab/blob/main/report/REPORT.md"


def test_directory_artifacts_link_to_tree(raw):
    raw["services"][0]["artifact"]["path"] = "labs/"
    catalog = parse(raw)
    assert catalog.artifact_url(catalog.services[0]).endswith("/tree/main/labs")


def test_folded_text_is_normalized(raw):
    raw["services"][0]["problem"] = "Untrusted\n  Terraform.\n"
    assert parse(raw).services[0].problem == "Untrusted Terraform."


@pytest.mark.parametrize(
    ("description", "fragment"),
    [
        ("Shows a rescue through a report; verified offline.", "description must read"),
        ("Demonstrates a rescue with a report; verified offline.", "description must read"),
        ("Demonstrates a rescue through a report, verified offline.", "description must read"),
        ("Demonstrates a rescue through a report; verified offline", "description must read"),
        ("Demonstrates a rescue through a report; verified " + "x" * 350 + ".", "characters"),
    ],
)
def test_description_pattern(raw, description, fragment):
    raw["services"][0]["repo"]["description"] = description
    errors = repo_rule_errors(parse(raw).services[0].repo)
    assert any(fragment in e for e in errors)


@pytest.mark.parametrize(
    ("topics", "fragment"),
    [
        (["aws", "devops", "portfolio"], "missing required topic 'lab'"),
        (["aws", "devops", "lab"], "missing required topic 'portfolio'"),
        (["aws", "devops", "portfolio", "lab", "Terraform"], "not a valid GitHub topic"),
        (["aws", "devops", "portfolio", "lab", "lab"], "duplicate topics"),
        (["aws", "devops", "portfolio", "lab", *(f"t{i}" for i in range(7))], "11 topics"),
    ],
)
def test_topic_rules(raw, topics, fragment):
    raw["services"][0]["repo"]["topics"] = topics
    errors = repo_rule_errors(parse(raw).services[0].repo)
    assert any(fragment in e for e in errors)


def test_sample_kind_requires_sample_deliverable_topic(raw):
    raw["services"][0]["repo"]["kind"] = "sample"
    errors = repo_rule_errors(parse(raw).services[0].repo)
    assert "example-lab: missing required topic 'sample-deliverable'" in errors


def test_duplicates_are_reported(raw):
    raw["services"].append(raw["services"][0])
    errors = catalog_rule_errors(parse(raw))
    assert "duplicate service id: audit" in errors
    assert "duplicate offer: Terraform audit and fix" in errors
    assert "duplicate repository name: example-lab" in errors


@pytest.mark.parametrize("path", ["/etc/passwd", "../other/README.md"])
def test_artifact_path_stays_inside_the_repository(raw, path):
    raw["services"][0]["artifact"]["path"] = path
    assert any("artifact path must be relative" in e for e in catalog_rule_errors(parse(raw)))


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda r: r.update(services=[]), "'services' must be a non-empty list"),
        (lambda r: r["services"][0].pop("problem"), "'problem' must be a non-empty string"),
        (lambda r: r["services"][0]["repo"].update(status="done"), "status 'done'"),
        (lambda r: r["services"][0]["repo"].update(kind="demo"), "kind 'demo'"),
        (lambda r: r["services"][0]["repo"].update(topics="aws"), "'topics' must be a list"),
        (lambda r: r["services"][0]["repo"].update(local="../outside"), "'local' must be a folder name"),
        (lambda r: r["services"][0].update(id="../x"), "id '../x' must be lowercase"),
        (lambda r: r["services"][0]["repo"].update(name="Example_Lab"), "repository name 'Example_Lab'"),
        (lambda r: r.update(more=None), "'more' must be a list"),
        (lambda r: r.update(more=False), "'more' must be a list"),
        (lambda r: r["services"][0]["repo"].update(standard=False), "only for repositories under 'more'"),
    ],
)
def test_structural_errors_raise(raw, mutate, message):
    mutate(raw)
    with pytest.raises(CatalogError, match=message):
        parse(raw)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("CI/CD pipeline for your deployments", "cicd-pipeline-for-your-deployments"),
        ("Kubernetes on AWS EKS", "kubernetes-on-aws-eks"),
        ("DevOps and Well-Architected assessment", "devops-and-well-architected-assessment"),
    ],
)
def test_anchor_matches_github(title, expected):
    assert anchor(title) == expected


def test_profile_url_is_checked(raw):
    raw["profile_url"] = "https://example.com/profile"
    assert "profile_url must be an Upwork freelancer profile" in catalog_rule_errors(parse(raw))


def test_duplicate_yaml_keys_are_rejected():
    text = "services:\n  - id: audit\n    artifact:\n      path: a.md\n      path: b.md\n"
    with pytest.raises(CatalogError, match="duplicate keys 'path' \\(line 5\\)"):
        loads(text)


def test_catalog_without_more_parses(raw):
    raw.pop("more")
    assert parse(raw).more == ()
