"""Nested citation templates must not leave braces behind as drop notes."""

import json
from pathlib import Path

import pytest

from scripts.drops import drops_wikitext


def test_cached_evil_chicken_quantity_note_has_no_template_residue():
    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text(encoding="utf-8")
    )
    feather = next(
        drop
        for table in drops_wikitext.parse_all_drop_tables(pages["Evil Chicken"])
        for drop in table.drops
        if drop.name == "Feather"
    )
    assert feather.quantity == "3-242"
    assert feather.notes == [
        "The quantity of dropped feathers is equal to your combat level, plus a "
        "random amount between 0 and 86. The amount given is increased by 30 "
        "when wearing a ring of wealth."
    ]


def test_nested_citation_removal_preserves_note_and_literal_outside_text():
    assert drops_wikitext.parse_inline_note_fields(
        "Before the footnote. "
        "{{Refn|group=d|Only dropped on a [[bounty task]]."
        "{{CiteDiscord|author=Mod Example|quote=Source evidence}}}} "
        "After the footnote."
    ) == [
        "Only dropped on a bounty task.",
        "Before the footnote. After the footnote.",
    ]


def test_multiple_nested_refn_templates_leave_no_extra_notes():
    assert drops_wikitext.parse_inline_note_fields(
        "{{Refn|group=d|First condition.{{CiteNews|title=First source}}}}"
        "{{refn|group=d|Second condition.{{CiteDiscord|quote=Second source}}}}"
    ) == ["First condition.", "Second condition."]


def test_rejected_refn_group_leaves_no_nested_template_residue():
    assert (
        drops_wikitext.parse_inline_note_fields(
            "{{Refn|group=x|Citation only.{{CiteNews|title=Source}}}}"
        )
        == []
    )


@pytest.mark.parametrize("attrs", ["", ' group="e"', ' group="d"'])
def test_explicit_inline_ref_conditions_keep_their_existing_group_semantics(attrs):
    assert drops_wikitext.parse_inline_note_fields(
        f"<ref{attrs}>Only dropped on a bounty task.</ref>"
    ) == ["Only dropped on a bounty task."]
