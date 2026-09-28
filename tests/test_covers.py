import shutil

import pytest

from conftest import INDEX_ROOT, make_repo
from portfolio_check import checks
from portfolio_check.covers import COVER_SIZE, refresh
from portfolio_check.model import parse


@pytest.fixture
def layout(tmp_path, raw):
    index = tmp_path / "index"
    (index / "assets").mkdir(parents=True)
    make_repo(tmp_path / "example-lab-folder")
    return parse(raw), index, tmp_path


def test_refresh_writes_a_card_that_passes_the_check(layout):
    catalog, index, root = layout
    assert refresh(catalog, index, root, {}) == ["copied audit.png from example-lab"]
    assert checks.png_size(index / "assets/audit.png") == COVER_SIZE
    assert [r.status for r in checks.cover_results(catalog, index, root)] == ["pass"]


def test_override_is_used_when_given(layout):
    catalog, index, root = layout
    assert refresh(catalog, index, root, {"audit": INDEX_ROOT / "assets/eks.png"}) == ["copied audit.png from eks.png"]
    assert checks.cover_results(catalog, index, root)[0].status == "FAIL"  # differs from the repository cover


def test_missing_override_raises(layout):
    catalog, index, root = layout
    with pytest.raises(FileNotFoundError, match="does not exist"):
        refresh(catalog, index, root, {"audit": root / "typo.png"})


def test_missing_source_keeps_an_existing_card(layout):
    catalog, index, root = layout
    refresh(catalog, index, root, {})
    shutil.rmtree(root / "example-lab-folder")
    assert refresh(catalog, index, root, {})[0].startswith("kept   audit.png")


def test_missing_source_without_card_raises(layout):
    catalog, index, root = layout
    shutil.rmtree(root / "example-lab-folder")
    with pytest.raises(FileNotFoundError, match="pass --source audit=PATH"):
        refresh(catalog, index, root, {})
