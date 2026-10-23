"""Mentioning a free-to-play world does not make an entire note F2P-only."""

import json
from pathlib import Path

import pytest

from scripts.drops import drops_wikitext


def test_cached_moss_giant_mossy_key_retains_mixed_world_rates():
    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text(encoding="utf-8")
    )
    key = next(
        drop
        for table in drops_wikitext.parse_all_drop_tables(pages["Moss giant"])
        for drop in table.drops
        if drop.name == "Mossy key"
    )
    assert key.rarity == "1/150"
    note = " ".join(key.notes)
    assert "Slayer task" in note
    assert "1/75" in note
    assert "free-to-play world" in note
    assert "1/100" in note
    assert "off-task in the Wilderness" in note
    assert "}}" not in note


@pytest.mark.parametrize(
    "note",
    [
        "This also applies on a free-to-play world.",
        "On a free to play world, the drop rate is 1/75; otherwise it is 1/100.",
    ],
)
def test_ordinary_and_mixed_world_notes_keep_existing_classification(note):
    classified = drops_wikitext.classify_note(note, "Mossy key")
    assert classified.as_list() == [note]
    if "1/75" in note:
        assert classified.transform_rate == [note]
    else:
        assert classified.condition == [note]


@pytest.mark.parametrize("note", ["", "  \n  ", "Only dropped in free-to-play."])
def test_blank_and_explicit_free_to_play_only_notes_stay_suppressed(note):
    assert drops_wikitext.classify_note(note, "Coins").as_list() == []


def test_explicit_free_to_play_only_drop_still_does_not_enter_members_table():
    source = (
        "{{Infobox Monster|id=1}}\n==Drops==\n===Other===\n"
        "{{DropsLine|name=Coins|quantity=2|rarity=1/2|raritynotes="
        "{{Refn|group=d|Only dropped in free-to-play.}}}}"
    )
    assert drops_wikitext.parse_all_drop_tables(source)[0].drops == []


@pytest.mark.parametrize("field", ["namenotes", "raritynotes"])
def test_named_cached_mossy_key_note_retains_both_mixed_world_rates(field):
    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text(encoding="utf-8")
    )
    params = next(
        params
        for _, params in drops_wikitext.extract_templates(
            pages["Moss giant"], "DropsLine"
        )
        if params.get("name") == "Mossy key"
    )
    _, refn = drops_wikitext.extract_templates(params["raritynotes"], "Refn")[0]
    note = refn["_0"]
    source = (
        "{{Infobox Monster|id=1}}\n==Drops==\n===Other===\n"
        "{{DropsLine|name=Mossy key|quantity=1|rarity=1/150|"
        + field
        + '=<ref name="mixed" group="d" />}}\n'
        + '<ref name="mixed" group="d">'
        + note
        + "</ref>"
    )
    drop = drops_wikitext.parse_all_drop_tables(source)[0].drops[0]
    assert drop.name == "Mossy key"
    assert drop.rarity == "1/150"
    preserved = " ".join(drop.notes)
    assert "1/75" in preserved
    assert "free-to-play world" in preserved
    assert "1/100" in preserved
    assert "off-task in the Wilderness" in preserved


@pytest.mark.parametrize("field", ["namenotes", "raritynotes"])
def test_named_explicit_free_to_play_only_drop_is_still_filtered(field):
    source = (
        "{{Infobox Monster|id=1}}\n==Drops==\n===Other===\n"
        "{{DropsLine|name=Coins|quantity=2|rarity=1/2|"
        + field
        + '=<ref name="world" group="d" />}}\n'
        + '<ref name="world" group="d">Only dropped in free-to-play.</ref>'
    )
    assert drops_wikitext.parse_all_drop_tables(source)[0].drops == []
