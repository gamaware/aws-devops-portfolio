"""Read-only comparison of the catalog with the live GitHub repositories (make test-live; needs the network)."""

from __future__ import annotations

import http
import http.client
import json
import os

from .checks import Result
from .model import Catalog, Repo

QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    description
    visibility
    usesCustomOpenGraphImage
    repositoryTopics(first: 20) { nodes { topic { name } } }
  }
}
"""


def fetch(owner: str, name: str, token: str) -> dict | None:
    """One repository's public settings from the GitHub GraphQL API, or None when it does not exist."""
    body = json.dumps({"query": QUERY, "variables": {"owner": owner, "name": name}})
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "portfolio-check"}
    connection = http.client.HTTPSConnection("api.github.com", timeout=30)
    try:
        connection.request("POST", "/graphql", body=body, headers=headers)
        response = connection.getresponse()
        if response.status != http.HTTPStatus.OK:
            raise RuntimeError(f"GitHub API returned HTTP {response.status} for {owner}/{name}")
        payload = json.load(response)
    finally:
        connection.close()
    errors = payload.get("errors") or []
    if any(e.get("type") == "NOT_FOUND" for e in errors):
        return None
    if errors:
        raise RuntimeError(f"GitHub API error for {owner}/{name}: {errors[0].get('message')}")
    return payload["data"]["repository"]


def compare(repo: Repo, live: dict | None) -> list[Result]:
    if live is None:
        return [Result("FAIL", f"{repo.name}: not found on GitHub")]
    results = [Result("pass" if live["visibility"] == "PUBLIC" else "FAIL", f"{repo.name}: {live['visibility']}")]
    if not repo.standard:
        return [*results, Result("skip", f"{repo.name}: extra repository, settings left unchanged")]
    topics = sorted(n["topic"]["name"] for n in live["repositoryTopics"]["nodes"])
    for ok, message in (
        (live["description"] == repo.description, f"{repo.name}: description matches the catalog"),
        (topics == sorted(repo.topics), f"{repo.name}: topics match the catalog"),
        (live["usesCustomOpenGraphImage"], f"{repo.name}: custom social preview uploaded"),
    ):
        results.append(Result("pass" if ok else "FAIL", message))
    return results


def run(catalog: Catalog) -> list[Result]:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("set GITHUB_TOKEN (make test-live reads it from `gh auth token`)")
    results = []
    for repo in catalog.all_repos():
        results.extend(compare(repo, fetch(catalog.owner, repo.name, token)))
    return results
