"""Load data/catalog.yaml and validate it against the portfolio rules that need no other repository."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

# STANDARD section 5: "Demonstrates <capability> through <artifact>; verified <scope>."
DESCRIPTION_RE = re.compile(r"^Demonstrates \S.* through \S.*; verified \S.*\.$")
# GitHub limits: descriptions to 350 characters, topics to lowercase letters, digits and hyphens, 50 characters.
DESCRIPTION_MAX = 350
TOPIC_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")
TOPICS_MAX = 10
REQUIRED_TOPICS = ("aws", "devops", "portfolio")
KIND_TOPIC = {"lab": "lab", "labs": "lab", "sample": "sample-deliverable", "index": None}
STATUSES = ("ready", "in-progress")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REPO_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class CatalogError(ValueError):
    """The catalog is malformed or breaks a rule."""


@dataclass(frozen=True)
class Repo:
    name: str
    local: str
    kind: str
    status: str
    standard: bool
    description: str
    topics: tuple[str, ...]


@dataclass(frozen=True)
class Artifact:
    label: str
    path: str
    summary: str


@dataclass(frozen=True)
class Service:
    id: str
    offer: str
    problem: str
    repo: Repo
    artifact: Artifact
    verification: str


@dataclass(frozen=True)
class Extra:
    repo: Repo
    summary: str


@dataclass(frozen=True)
class Catalog:
    owner: str
    profile_url: str
    index: Repo
    services: tuple[Service, ...]
    more: tuple[Extra, ...]

    def repo_url(self, repo: Repo) -> str:
        return f"https://github.com/{self.owner}/{repo.name}"

    def artifact_url(self, service: Service) -> str:
        view = "tree" if service.artifact.path.endswith("/") else "blob"
        return f"{self.repo_url(service.repo)}/{view}/main/{service.artifact.path.rstrip('/')}"

    def all_repos(self) -> tuple[Repo, ...]:
        return (self.index, *(s.repo for s in self.services), *(e.repo for e in self.more))


def _text(node: dict, key: str, where: str) -> str:
    value = node.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{where}: '{key}' must be a non-empty string")
    return " ".join(value.split())


def _repo(node: object, where: str, *, extra: bool = False) -> Repo:
    if not isinstance(node, dict):
        raise CatalogError(f"{where}: 'repo' must be a mapping")
    name = _text(node, "name", where)
    if not REPO_NAME_RE.match(name):
        raise CatalogError(f"{where}: repository name '{name}' must be lowercase words joined by hyphens")
    topics = node.get("topics")
    if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
        raise CatalogError(f"{where}: 'topics' must be a list of strings")
    status = node.get("status", "ready")
    if status not in STATUSES:
        raise CatalogError(f"{where}: status '{status}' is not one of {', '.join(STATUSES)}")
    kind = _text(node, "kind", where)
    if kind not in KIND_TOPIC:
        raise CatalogError(f"{where}: kind '{kind}' is not one of {', '.join(KIND_TOPIC)}")
    standard = node.get("standard", True)
    if not isinstance(standard, bool):
        raise CatalogError(f"{where}: 'standard' must be true or false")
    if not standard and not extra:
        raise CatalogError(f"{where}: 'standard: false' is allowed only for repositories under 'more'")
    local = node.get("local", name)
    if not isinstance(local, str) or not REPO_NAME_RE.match(local):
        raise CatalogError(f"{where}: 'local' must be a folder name of lowercase words joined by hyphens")
    return Repo(
        name=name,
        local=local,
        kind=kind,
        status=status,
        standard=standard,
        description=_text(node, "description", where),
        topics=tuple(topics),
    )


def _service(node: object, position: int) -> Service:
    if not isinstance(node, dict):
        raise CatalogError(f"services[{position}]: must be a mapping")
    where = f"services[{position}]"
    sid = _text(node, "id", where)
    if not SLUG_RE.match(sid):
        raise CatalogError(f"{where}: id '{sid}' must be lowercase words joined by hyphens")
    where = f"service '{sid}'"
    artifact = node.get("artifact")
    if not isinstance(artifact, dict):
        raise CatalogError(f"{where}: 'artifact' must be a mapping")
    return Service(
        id=sid,
        offer=_text(node, "offer", where),
        problem=_text(node, "problem", where),
        repo=_repo(node.get("repo"), where),
        artifact=Artifact(
            label=_text(artifact, "label", where),
            path=_text(artifact, "path", where),
            summary=_text(artifact, "summary", where),
        ),
        verification=_text(node, "verification", where),
    )


def parse(raw: object) -> Catalog:
    """Build a Catalog from parsed YAML, raising CatalogError on structural problems."""
    if not isinstance(raw, dict):
        raise CatalogError("catalog: top level must be a mapping")
    services = raw.get("services")
    if not isinstance(services, list) or not services:
        raise CatalogError("catalog: 'services' must be a non-empty list")
    more = raw.get("more", [])
    if not isinstance(more, list):
        raise CatalogError("catalog: 'more' must be a list")
    extras = []
    for position, node in enumerate(more):
        if not isinstance(node, dict):
            raise CatalogError(f"more[{position}]: must be a mapping")
        where = f"more[{position}]"
        extras.append(Extra(repo=_repo(node.get("repo"), where, extra=True), summary=_text(node, "summary", where)))
    return Catalog(
        owner=_text(raw, "owner", "catalog"),
        profile_url=_text(raw, "profile_url", "catalog"),
        index=_repo(raw.get("index"), "index"),
        services=tuple(_service(node, i) for i, node in enumerate(services)),
        more=tuple(extras),
    )


class _UniqueKeyLoader(yaml.SafeLoader):
    """A SafeLoader that rejects a mapping whose keys construct to the same value, such as `true:` and `True:`."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        seen = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=True)
            try:
                duplicate = key in seen
            except TypeError:
                continue  # an unhashable key; the base constructor reports it
            if duplicate:
                raise CatalogError(f"catalog: duplicate keys '{key_node.value}' (line {key_node.start_mark.line + 1})")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def loads(text: str) -> Catalog:
    """Parse catalog YAML text. Plain YAML loaders keep the last of two equal keys, so duplicates are rejected."""
    loader = _UniqueKeyLoader(text)
    try:
        return parse(loader.get_single_data())
    finally:
        loader.dispose()


def load(path: Path) -> Catalog:
    return loads(path.read_text(encoding="utf-8"))


def repo_rule_errors(repo: Repo) -> list[str]:
    """Description and topic rules for one repository (STANDARD section 5)."""
    errors = []
    if not DESCRIPTION_RE.match(repo.description):
        errors.append(
            f"{repo.name}: description must read 'Demonstrates <capability> through <artifact>; verified <scope>.'"
        )
    if len(repo.description) > DESCRIPTION_MAX:
        errors.append(
            f"{repo.name}: description has {len(repo.description)} characters (GitHub allows {DESCRIPTION_MAX})"
        )
    if len(repo.topics) > TOPICS_MAX:
        errors.append(f"{repo.name}: {len(repo.topics)} topics (at most {TOPICS_MAX})")
    if len(set(repo.topics)) != len(repo.topics):
        errors.append(f"{repo.name}: duplicate topics")
    errors.extend(f"{repo.name}: topic '{t}' is not a valid GitHub topic" for t in repo.topics if not TOPIC_RE.match(t))
    required = [*REQUIRED_TOPICS]
    if KIND_TOPIC[repo.kind]:
        required.append(KIND_TOPIC[repo.kind])
    errors.extend(f"{repo.name}: missing required topic '{t}'" for t in required if t not in repo.topics)
    return errors


def catalog_rule_errors(catalog: Catalog) -> list[str]:
    """Rules across the whole catalog that need no file outside data/catalog.yaml."""
    errors = []
    if not catalog.profile_url.startswith("https://www.upwork.com/freelancers/~"):
        errors.append("profile_url must be an Upwork freelancer profile")
    for field, values in (
        ("service id", [s.id for s in catalog.services]),
        ("offer", [s.offer for s in catalog.services]),
        ("repository name", [r.name for r in catalog.all_repos()]),
        ("local folder", [r.local for r in catalog.all_repos()]),
    ):
        duplicates = sorted({v for v in values if values.count(v) > 1})
        errors.extend(f"duplicate {field}: {d}" for d in duplicates)
    for service in catalog.services:
        if service.artifact.path.startswith("/") or ".." in Path(service.artifact.path).parts:
            errors.append(f"service '{service.id}': artifact path must be relative to the repository root")
    for repo in catalog.all_repos():
        errors.extend(repo_rule_errors(repo))
    return errors
