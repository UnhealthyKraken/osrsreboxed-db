"""
Author:  Toby Wisener
Email:   tobywisener@googlemail.com

Description:
Tests for module: scripts/drops

Copyright (c) 2026, Toby Wisener

###############################################################################
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
"""

from scripts.drops import drops_tables, drops_wikitext


class FakeItem:
    """Stand-in for an osrsreboxed item, so the tests need no item database."""

    def __init__(self, item_id, name, wiki_name=None, tradeable_on_ge=True):
        self.id = item_id
        self.name = name
        self.wiki_name = wiki_name or name
        self.tradeable_on_ge = tradeable_on_ge
        self.duplicate = False
        self.noted = False
        self.placeholder = False
        self.stacked = None


ITEMS = drops_tables.ItemIdLookup(
    [
        FakeItem(526, "Bones"),
        FakeItem(995, "Coins"),
        FakeItem(617, "Coins", "Coins (Shilo Village)", tradeable_on_ge=False),
        FakeItem(1163, "Rune full helm"),
        FakeItem(11286, "Draconic visage"),
        FakeItem(5072, "Bird nest", "Bird nest (egg) (Blue egg)"),
    ]
)

WIKITEXT = """
{{Infobox Monster
|id1 = 123,124
|version1 = Normal
}}

==Drops==
===100%===
{{DropsLine|name=Bones|quantity=1|rarity=Always}}

===Weapons and armour===
{{DropsLine|name=Rune full helm|quantity=1|rarity=3/128}}
{{DropsLine|name=Coins|quantity=100-200|rarity=1/128}}
{{DropsLine|name=Nothing|rarity=123/128}}
{{RareDropTable|1/128}}
{{DropsLine|name=Bird nest (egg)#Blue egg|quantity=1|rarity=Common}}

===Tertiary===
{{DropsLine|name=Draconic visage|quantity=1|rarity=1/{{#expr:5000/(1)}}
|raritynotes=Only dropped in [[Wilderness|the Wilderness]].}}

==Other==
"""


def _table():
    tables = drops_wikitext.parse_all_drop_tables(WIKITEXT)
    assert len(tables) == 1
    return drops_tables.build_table_json(
        drops_tables.build_table_spec("Test_monster", tables[0], ITEMS)
    )


def test_npc_ids_come_from_the_infobox():
    """Both IDs on the infobox roll the page's single drop table."""
    tables = drops_wikitext.parse_all_drop_tables(WIKITEXT)
    assert tables[0].npc_ids == [123, 124]


def test_table_identity():
    """Table naming follows the wiki page, not the npc."""
    table = _table()
    assert table["table_id"] == "test_monster"
    assert table["table_name"] == "Test monster Drops"
    assert table["wiki_page"] == "Test monster"
    assert table["label"] == "Drops"


def test_guaranteed_drop_has_no_rate():
    """A 100% drop is exported as always, with no weight or roll."""
    entry = _table()["entries"][0]
    assert entry["item_id"] == 526
    assert entry["always"] is True
    assert "weight" not in entry and "out_of" not in entry


def test_main_table_weights_share_one_denominator():
    """Every main table drop is weighted against the same pool."""
    table = _table()
    assert table["main_max_roll"] == 128
    entries = [e for e in table["entries"] if e.get("out_of") == 128]
    assert [e.get("name") for e in entries] == [
        "Rune full helm",
        "Coins",
        None,  # the Nothing roll
        None,  # the rare drop table access
    ]
    assert entries[0]["weight"] == 3
    assert entries[0]["rarity"] == 0.0234375
    assert entries[1]["quantity"] == [100, 200]
    assert entries[2]["nothing"] is True
    assert entries[3]["shared_table"] == "rareDrop"


def test_item_ids_prefer_the_wiki_name():
    """ "Coins" is four items; the one the wiki links to wins."""
    coins = [e for e in _table()["entries"] if e.get("name") == "Coins"][0]
    assert coins["item_id"] == 995


def test_version_anchors_resolve_to_the_right_item():
    """``Bird nest (egg)#Blue egg`` is the blue egg item, not the base nest."""
    nest = [
        e for e in _table()["entries"] if e.get("name", "").startswith("Bird nest")
    ][0]
    assert nest["item_id"] == 5072
    # A word rarity is a convention, not wiki data, so it is flagged.
    assert nest["assumed_rarity"] is True
    # Its 1/8 rate is not the table pool, so it rolls separately.
    assert nest["separate_roll"] is True
    assert nest["out_of"] == 8


def test_tertiary_rate_is_evaluated_and_annotated():
    """Wiki arithmetic resolves to a rate, and footnotes travel with the drop."""
    tertiary = _table()["tertiary"][0]
    assert tertiary["item_id"] == 11286
    assert tertiary["out_of"] == 5000
    assert tertiary["notes"] == ["Only dropped in the Wilderness."]


def test_expression_evaluation_rejects_non_arithmetic():
    """The expression evaluator only ever evaluates arithmetic."""
    assert drops_wikitext.evaluate_expression("2000/(1999/2000) round 1") == "2001"
    assert drops_wikitext.evaluate_expression("__import__('os')") is None


def test_shared_table_accesses_are_not_double_counted():
    """A table that rolls the seed table drops its individually listed seeds."""
    wikitext = """{{Infobox Monster\n|id1 = 1\n}}\n==Drops==\n"""
    wikitext += "===Seeds===\n{{GeneralSeedDropTableInfo|18/128}}\n"
    wikitext += "{{DropsLine|name=Coins|quantity=1|rarity=1/128}}\n"
    table = drops_wikitext.parse_all_drop_tables(wikitext)[0]
    exported = drops_tables.build_table_json(
        drops_tables.build_table_spec("Test_monster", table, ITEMS)
    )
    assert [e.get("shared_table") for e in exported["entries"]] == ["seed"]


def test_cached_variant_pages_keep_npc_ids_separate():
    import json
    from pathlib import Path

    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text()
    )
    expected = {
        "Rogue": {"Level 15 drops": {526}, "Level 135 drops": {6603}},
        "Giant rat": {
            "Level 3 and 6 drops": set(range(2856, 2865)),
            "Level 26 drops": {2510, 2511, 2512},
        },
        "Skeleton": {
            "Drops (Plain)": {
                71,
                72,
                73,
                75,
                76,
                78,
                79,
                80,
                81,
                83,
                14426,
                14427,
                14428,
            },
            "Drops (Unarmed)": {70, 74},
            "Drops (Armed)": {77, 82},
        },
        "Rat": {
            "Drops (Regular)": {2854, 2855},
            "Drops (Stronghold of Security)": {2492, 2513},
        },
    }
    for page, mappings in expected.items():
        actual = {
            table.table_name: set(table.npc_ids)
            for table in drops_wikitext.parse_all_drop_tables(pages[page])
        }
        assert actual == mappings, page


def test_variant_matching_uses_whole_words_and_numbers():
    assert not drops_wikitext._heading_matches_drop_version("Unarmed", "Armed")
    assert not drops_wikitext._heading_matches_drop_version("Level 135", "Level 13")


def test_non_guaranteed_rarity_under_guaranteed_heading():
    source = WIKITEXT.replace("rarity=Always", "rarity=Varies")
    table = drops_wikitext.parse_all_drop_tables(source)[0]
    result = drops_tables.build_table_json(
        drops_tables.build_table_spec("Test", table, ITEMS)
    )
    assert not any(entry.get("item_id") == 526 for entry in result["entries"])
    bones = next(entry for entry in result["tertiary"] if entry["item_id"] == 526)
    assert bones["out_of"] == 128
    assert not bones.get("always")


def test_named_exceptions_and_level_ranges():
    import json
    from pathlib import Path

    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text()
    )
    for page in (
        "Highwayman",
        "Hobgoblin",
        "Tortoise",
        "Possessed pickaxe",
        "Lesser demon",
        "Zombie (Tarn's Lair)",
    ):
        tables = drops_wikitext.parse_all_drop_tables(pages[page])
        seen = set()
        for table in tables:
            assert table.npc_ids, (page, table.table_name)
            assert not seen.intersection(table.npc_ids), page
            seen.update(table.npc_ids)
    lesser = drops_wikitext.parse_all_drop_tables(pages["Lesser demon"])
    assert set(lesser[1].npc_ids) == {7865, 7866, 7867}
    zombies = drops_wikitext.parse_all_drop_tables(pages["Zombie (Tarn's Lair)"])
    assert zombies[0].npc_ids == list(range(6449, 6454))
    assert zombies[1].npc_ids == list(range(6454, 6460))


def test_noted_drops_are_flagged():
    """A wiki quantity ending in ``(noted)`` keeps its range and exports ``noted``."""
    page = """
{{Infobox Monster
|id1 = 125
}}

==Drops==
===Other===
{{DropsLine|name=Coins|quantity=100-200 (noted)|rarity=1/2}}
{{DropsLine|name=Bones|quantity=5|rarity=1/2}}
"""
    tables = drops_wikitext.parse_all_drop_tables(page)
    table = drops_tables.build_table_json(
        drops_tables.build_table_spec("Noted_monster", tables[0], ITEMS)
    )
    coins, bones = table["entries"]
    assert coins["quantity"] == [100, 200]
    assert coins["noted"] is True
    assert "quantity_raw" not in coins
    assert "noted" not in bones


def test_pre_roll_exports_resolved_denominators():
    """Pre-roll rates survive the main-rate resolver and independent rolls."""
    page = """{{Infobox Monster|id=1}}
==Drops==
===Pre-roll===
{{DropsLine|name=Coins|quantity=1|rarity=3/100}}
{{DropsLine|name=Bones|quantity=1|rarity=97/100}}
{{DropsLine|name=Rune full helm|quantity=1|rarity=1/500}}
===Other===
{{DropsLine|name=Coins|quantity=5|rarity=1/128}}
"""
    parsed = drops_wikitext.parse_all_drop_tables(page)[0]
    table = drops_tables.build_table_json(
        drops_tables.build_table_spec("Test", parsed, ITEMS)
    )
    coins, bones, main_coins, helm = table["entries"]
    assert coins["out_of"] == 100
    assert coins["rarity"] == 0.03
    assert bones["out_of"] == 100
    assert bones["rarity"] == 0.97
    assert coins["pre_roll"] and bones["pre_roll"]
    assert "separate_roll" not in coins
    assert main_coins["out_of"] == 128
    assert helm["out_of"] == 500
    assert helm["pre_roll"] and helm["separate_roll"]


def test_nothing_keeps_pre_roll_and_separate_roll_execution_flags():
    """Nothing on an independent roll must never enter the main weight pool."""
    page = """{{Infobox Monster|id=1}}
==Drops==
===Pre-roll===
{{DropsLine|name=Nothing|rarity=9/10}}
===Other===
{{DropsLine|name=Coins|quantity=1|rarity=64/128}}
{{DropsLine|name=Bones|quantity=1|rarity=64/128}}
{{DropsLine|name=Nothing|rarity=499/500}}
"""
    parsed = drops_wikitext.parse_all_drop_tables(page)[0]
    table = drops_tables.build_table_json(
        drops_tables.build_table_spec("Test", parsed, ITEMS)
    )
    pre_roll, _, _, separate = table["entries"]
    assert pre_roll["nothing"] and pre_roll["pre_roll"]
    assert pre_roll["out_of"] == 10
    assert separate["nothing"] and separate["separate_roll"]
    assert separate["out_of"] == 500
    assert "pre_roll" not in separate
    pool = [
        entry
        for entry in table["entries"]
        if not entry.get("pre_roll") and not entry.get("separate_roll")
    ]
    assert sum(entry["weight"] for entry in pool) == table["main_max_roll"] == 128


def test_cached_herb_access_exports_conditional_roll_counts():
    import json
    from pathlib import Path

    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text()
    )
    expected = {
        "Aberrant spectre": [(1, 11), (2, 11), (3, 4)],
        "Chaos druid": [(1, 35), (2, 11)],
        "Elder Chaos druid": [(1, 15), (2, 20), (3, 15), (4, 5)],
        "Skeletal Wyvern": [(3, 1)],
        "Undead Druid": [(1, 1), (2, 1), (3, 1)],
        "Bloodthirsty Shadow Wyrm": [(2, 1)],
    }
    for page, weights in expected.items():
        parsed = drops_wikitext.parse_all_drop_tables(pages[page])[0]
        table = drops_tables.build_table_json(
            drops_tables.build_table_spec(page, parsed, ITEMS)
        )
        access = next(e for e in table["entries"] if e.get("shared_table") == "herb")
        assert access["roll_count_weights"] == [
            {"rolls": count, "weight": weight} for count, weight in weights
        ], page


def test_general_seed_export_preserves_combat_level_categories():
    import json
    from pathlib import Path

    source = json.loads(
        (
            Path(__file__).parents[1] / "data/drops/drop-tables-wiki-page-text.json"
        ).read_text()
    )["Drop table"]
    seed = drops_tables.export_shared_subtables(source, ITEMS)["seed"]
    assert seed["entries"] == []
    assert seed["combat_level_multiplier"] == 10
    categories = seed["categories"]
    assert [c["minimum"] for c in categories] == [0, 485, 728, 850, 947, 995]
    assert [c.get("maximum_exclusive") for c in categories] == [
        485,
        728,
        850,
        947,
        995,
        None,
    ]
    assert [len(c["entries"]) for c in categories] == [8, 7, 5, 6, 14, 4]
    assert categories[0]["entries"][0]["name"] == "Potato seed"
    assert categories[1]["entries"][0]["name"] == "Barley seed"


def test_drop_table_template_version_excludes_quest_npc_ids():
    import json
    from pathlib import Path

    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text()
    )
    table = drops_wikitext.parse_all_drop_tables(pages["Amoxliatl"])[0]
    assert table.npc_ids == [13685]


def test_single_header_version_does_not_exclude_inherited_regular_variants():
    import json
    from pathlib import Path

    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text()
    )
    crocodile = drops_wikitext.parse_all_drop_tables(pages["Crocodile"])
    assert 11582 in {npc for table in crocodile for npc in table.npc_ids}
    moss_giant = drops_wikitext.parse_all_drop_tables(pages["Moss giant"])
    assert {2090, 2091, 2092, 2093, 7262, 14422} <= {
        npc for table in moss_giant for npc in table.npc_ids
    }
