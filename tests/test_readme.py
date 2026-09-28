import pytest

from conftest import STANDARD_README
from portfolio_check import readme


def test_standard_readme_complies():
    assert readme.section_order_errors(STANDARD_README) == []


def test_executive_summary_opener_and_no_license_comply():
    text = STANDARD_README.replace("What this proves", "Executive summary").replace("## License", "")
    assert readme.section_order_errors(text) == []


def test_headings_inside_code_fences_are_ignored():
    text = STANDARD_README.replace("## Architecture", "## Architecture\n\n```text\n## not a heading\n```")
    assert readme.section_order_errors(text) == []


def test_longer_fence_keeps_inner_backticks_inside_the_block():
    block = "````markdown\n```bash\nmake verify\n```\n## not a heading\n````"
    text = STANDARD_README.replace("## Architecture", f"## Architecture\n\n{block}")
    assert readme.section_order_errors(text) == []


def test_tilde_fence_is_not_closed_by_backticks():
    text = STANDARD_README.replace("## Architecture", "## Architecture\n\n~~~\n```\n## not a heading\n~~~")
    assert readme.section_order_errors(text) == []


def test_wrong_opener_is_reported():
    text = STANDARD_README.replace("What this proves", "Overview")
    assert readme.section_order_errors(text) == [
        "first section is 'Overview', expected one of: What this proves, Executive summary"
    ]


def test_missing_and_extra_sections_are_reported():
    text = STANDARD_README.replace("## Repository map", "## Layout")
    assert readme.section_order_errors(text) == [
        "missing sections: Repository map",
        "sections outside the standard: Layout",
    ]


def test_swapped_sections_are_reported():
    text = STANDARD_README.replace("## Architecture", "## TMP").replace("## Verify locally", "## Architecture")
    text = text.replace("## TMP", "## Verify locally")
    assert readme.section_order_errors(text)[0].startswith("sections out of order: ")


def test_empty_readme_is_reported():
    assert readme.section_order_errors("# Title only\n") == ["no level-two headings"]


def test_replace_generated_keeps_the_rest():
    text = f"before\n{readme.BEGIN}\nold\n{readme.END}\nafter\n"
    assert readme.replace_generated(text, "new\n") == f"before\n{readme.BEGIN}\nnew\n{readme.END}\nafter\n"


def test_replace_generated_needs_both_markers():
    with pytest.raises(ValueError, match="markers"):
        readme.replace_generated(f"{readme.END}\n{readme.BEGIN}\n", "x")
