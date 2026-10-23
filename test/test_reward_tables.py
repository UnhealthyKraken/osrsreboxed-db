"""Reward-only templates must never silently become ordinary NPC kill loot."""

import json
from fractions import Fraction
from pathlib import Path

import pytest

from osrsreboxed import items_api
from scripts.drops import drops_wikitext
from scripts.drops.drops_tables import ItemIdLookup
from scripts.drops.reward_tables import export_reward_tables


@pytest.fixture(scope="module")
def source():
    return json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text(encoding="utf-8")
    )["The Mimic"]


@pytest.fixture(scope="module")
def rewards(source):
    return export_reward_tables({"The Mimic": source}, ItemIdLookup(items_api.load()))


def test_default_npc_parser_still_omits_reward_rows(source):
    tables = drops_wikitext.parse_all_drop_tables(source)
    assert len(tables) == 2
    assert all(
        [drop.name for drop in table.drops] == ["Mahogany plank"] for table in tables
    )


def test_reward_export_has_two_tiers_and_no_npc_bindings(rewards):
    assert rewards["schema_version"] == 1
    assert set(rewards["tables"]) == {"the_mimic_elite", "the_mimic_master"}
    assert "npcs" not in rewards
    for table in rewards["tables"].values():
        assert len(table["entries"]) == 31
        assert not any("npc_ids" in row for row in table["entries"])
        assert table["wiki_page"] == "The Mimic"
        assert all(row["item_id"] is not None for row in table["entries"])


@pytest.mark.parametrize("table_id", ["the_mimic_elite", "the_mimic_master"])
@pytest.mark.parametrize("rate_field", ["rarity_raw", "alternate_rarity_raw"])
def test_each_tier_first_and_later_bonus_probabilities_sum_exactly_to_one(
    rewards, table_id, rate_field
):
    rows = [
        row
        for row in rewards["tables"][table_id]["entries"]
        if row["section"] != "Tertiary" and row["rarity_raw"].lower() != "always"
    ]
    assert sum(Fraction(row[rate_field]) for row in rows) == 1


@pytest.mark.parametrize(
    "table_id, expected",
    [
        ("the_mimic_elite", [600, 480, 360, 240, 120]),
        ("the_mimic_master", [600, 500, 400, 300, 200, 100]),
    ],
)
def test_attempt_quantities_preserve_explicit_source_order(rewards, table_id, expected):
    death = next(
        row
        for row in rewards["tables"][table_id]["entries"]
        if row["name"] == "Death rune"
    )
    assert death["quantity_options"] == expected
    assert death["item_id"] == 560


def test_noted_supplies_and_conditional_scroll_case_are_preserved(rewards):
    rows = rewards["tables"]["the_mimic_elite"]["entries"]
    ranarr = next(row for row in rows if row["name"] == "Grimy ranarr weed")
    assert ranarr["noted"] is True
    case = next(row for row in rows if row["name"] == "Mimic scroll case")
    assert case["item_id"] == 30926
    assert case["section"] == "Tertiary"
    assert any("not opened" in note for note in case["notes"])


def test_ordinary_only_pages_are_not_exported():
    body = "{{Infobox Monster|id=1}}\n==Drops==\n{{DropsLine|name=Coins|quantity=5|rarity=Always}}"
    assert export_reward_tables({"Ordinary": body}, ItemIdLookup([]))["tables"] == {}


def test_unknown_quantity_is_retained_without_inventing_a_default():
    body = "{{Infobox Monster|id=1}}\n==Drops==\n{{DropsLineReward|name=Coins|quantity=8;10;12|rarity=1/2}}"
    row = next(
        iter(
            export_reward_tables({"Reward": body}, ItemIdLookup([]))["tables"].values()
        )
    )["entries"][0]
    assert row["quantity_raw"] == "8;10;12"
    assert "quantity" not in row
    assert row["item_id"] is None


def test_full_export_writes_rewards_separately(tmp_path, monkeypatch):
    from scripts.drops import update

    source = "{{Infobox Monster|id=1}}\n==Drops==\n{{DropsLineReward|name=Coins|quantity=5|rarity=Always}}"
    monkeypatch.setattr(update.items_api, "load", lambda: [])
    monkeypatch.setattr(update, "load_monster_wikitext", lambda: {"Reward": source})
    monkeypatch.setattr(update, "load_npc_cache_names", lambda: {})
    monkeypatch.setattr(update, "load_shared_table_wikitext", lambda **kwargs: "")
    update.generate(tmp_path)
    rewards = json.loads((tmp_path / "reward-tables.json").read_text())
    npc_drops = json.loads((tmp_path / "npc-drops.json").read_text())
    assert rewards["tables"]["reward"]["entries"][0]["name"] == "Coins"
    assert npc_drops["tables"] == {}


def test_reward_rows_outside_recognized_drop_sections_are_reported():
    body = "==Rewards==\n{{DropsLineReward|name=Coins|quantity=1|rarity=Always}}"
    output = export_reward_tables({"Reward": body}, ItemIdLookup([]))
    assert output["unparsed_reward_rows"] == {
        "Reward": {"source_rows": 1, "exported_rows": 0}
    }


def test_word_rarity_keeps_source_text_and_assumption_marker():
    body = "==Drops==\n{{DropsLineReward|name=Coins|quantity=1|rarity=Common}}"
    row = export_reward_tables({"Reward": body}, ItemIdLookup([]))["tables"]["reward"][
        "entries"
    ][0]
    assert row["rarity_raw"] == "Common"
    assert row["assumed_rarity"] is True
