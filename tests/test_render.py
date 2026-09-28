from conftest import INDEX_ROOT
from portfolio_check import render
from portfolio_check.model import load, parse


def test_card_has_the_four_fields_and_the_offer(raw):
    catalog = parse(raw)
    text = "\n".join(render.card(catalog, catalog.services[0]))
    assert "[![Terraform audit and fix](assets/audit.png)](https://github.com/example-owner/example-lab)" in text
    for field in ("Client problem", "Repository", "Strongest artifact", "Verification scope", "Upwork offer"):
        assert f"- **{field}:**" in text
    assert "[Terraform audit and fix on Upwork](https://www.upwork.com/freelancers/~0100000000000000000)" in text


def test_every_offer_links_to_the_profile(raw):
    block = render.cards_block(parse(raw))
    assert "services/product/" not in block
    assert block.count("https://www.upwork.com/freelancers/~0100000000000000000") == len(raw["services"])


def test_in_progress_repository_is_labelled(raw):
    raw["services"][0]["repo"]["status"] = "in-progress"
    catalog = parse(raw)
    assert "lab (in progress)" in render.cards_block(catalog)


def test_block_ends_with_a_blank_line_before_the_end_marker(raw):
    assert render.cards_block(parse(raw)).endswith("\n\n")


def test_real_catalog_renders_every_service_and_the_extra():
    catalog = load(INDEX_ROOT / "data/catalog.yaml")
    block = render.cards_block(catalog)
    assert block.count("\n### ") == len(catalog.services) + 1
    assert "https://github.com/gamaware/terraform-aws-rescue-lab" in block
    assert "terraform-aws-baseline-lab" not in block
    assert "services/product/" not in block
