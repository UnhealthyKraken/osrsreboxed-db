"""Quantity footnotes use the same note contract as name and rarity footnotes."""

import json
from pathlib import Path

import pytest

from scripts.drops import drops_wikitext


def parse_rows(rows):
    source = "{{Infobox Monster|id=1}}\n==Drops==\n===Other===\n" + rows
    return drops_wikitext.parse_all_drop_tables(source)[0].drops


@pytest.mark.parametrize(
    ("page", "quantity", "note"),
    [
        (
            "Narwhal",
            "3-7,5-10",
            "The quantity is increased to 5-10 while on a narwhal bounty task.",
        ),
        (
            "Orca",
            "4-8,7-11",
            "The quantity is increased while on an orca bounty task.",
        ),
    ],
)
def test_cached_bounty_quantity_notes_are_preserved(page, quantity, note):
    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text(encoding="utf-8")
    )
    drop = next(
        drop
        for table in drops_wikitext.parse_all_drop_tables(pages[page])
        for drop in table.drops
        if drop.name == "Dragon nails"
    )
    assert drop.quantity == quantity
    assert note in drop.notes


def test_inline_quantity_notes_deduplicate_without_losing_other_note_fields():
    drop = parse_rows(
        "{{DropsLine|name=Dragon nails|quantity=2|rarity=1/75"
        "|namenotes={{Refn|group=d|Only dropped on a bounty task.}}"
        "|raritynotes={{Refn|group=d|Dragon nails have a special drop rate.}}"
        "|quantitynotes={{Refn|group=d|Only dropped on a bounty task.}}"
        "{{Refn|group=d|The quantity increases on a bounty task.}}}}"
    )[0]
    assert drop.notes == [
        "Only dropped on a bounty task.",
        "The quantity increases on a bounty task.",
        "Dragon nails have a special drop rate.",
    ]


def test_named_quantity_refs_keep_generic_conditions_and_rarity_ref_filtering():
    drop = parse_rows(
        "{{DropsLine|name=Dragon nails|quantity=2|rarity=1/75"
        '|quantitynotes=<ref name="bounty" group="d" />'
        '|raritynotes=<ref name="bag" group="d" />}}\n'
        '<ref name="bounty" group="d">The quantity increases on a bounty task.</ref>\n'
        '<ref name="bag" group="d">Looting bags are only dropped in the Wilderness.</ref>'
    )[0]
    assert drop.notes == ["The quantity increases on a bounty task."]


def test_quantity_ref_definition_is_collected_and_reused_without_duplicate_notes():
    drops = parse_rows(
        "{{DropsLine|name=Dragon nails|quantity=2|rarity=1/75"
        '|quantitynotes=<ref name="bounty" group="d">'
        "Only dropped on a bounty task.</ref>}}\n"
        "{{DropsLine|name=Coins|quantity=3|rarity=1/75"
        '|quantitynotes=<ref name="bounty" group="d" />}}'
    )
    assert [drop.notes for drop in drops] == [
        ["Only dropped on a bounty task."],
        ["Only dropped on a bounty task."],
    ]


def test_noted_quantity_stays_separate_from_quantity_notes():
    drop = parse_rows(
        "{{DropsLine|name=Dragon nails|quantity=2-4 (noted)|rarity=1/75"
        "|quantitynotes={{Refn|group=d|Only dropped on a bounty task.}}}}"
    )[0]
    assert drop.quantity == "2-4"
    assert drop.is_noted is True
    assert drop.notes == ["Only dropped on a bounty task."]


def test_quantity_notes_preserve_free_to_play_drop_filtering():
    assert (
        parse_rows(
            "{{DropsLine|name=Coins|quantity=2|rarity=1/75"
            "|quantitynotes={{Refn|group=d|Only dropped in free-to-play.}}}}"
        )
        == []
    )
