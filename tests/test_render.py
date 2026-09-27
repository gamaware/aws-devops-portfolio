from conftest import INDEX_ROOT
from portfolio_check import render
from portfolio_check.model import load, parse


def test_card_has_the_four_fields_and_the_offer(raw):
    catalog = parse(raw)
    text = "\n".join(render.card(catalog, catalog.services[0]))
    assert "[![Terraform audit and fix cover](assets/audit.png)](https://github.com/example-owner/example-lab)" in text
    for field in ("Client problem", "Repository", "Strongest artifact", "Verification scope", "Upwork offer"):
        assert f"- **{field}:**" in text
    assert "[Terraform audit and fix](https://www.upwork.com/services/product/1000000000000000001)" in text


def test_pending_offer_has_no_link(raw):
    raw["services"][0]["offer_status"] = "pending"
    catalog = parse(raw)
    block = render.cards_block(catalog)
    assert "services/product/" not in block
    assert "(listing pending on Upwork)" in block


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
    assert "2104111946055354406" not in block  # the cost offer is still pending
