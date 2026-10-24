"""
Author:  Toby Wisener
Email:   tobywisener@googlemail.com

Description:
Tests for module: docs/drops-json

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

import json
from pathlib import Path

import config
import validator


def _load(file_name: str):
    """Load one of the generated drops dump files."""
    with open(Path(config.DOCS_DROPS_PATH / file_name), "r", encoding="utf-8") as f:
        return json.load(f)


def test_drops_docs_json_exists_and_valid():
    """Ensure the drops dump files are generated into docs."""
    for file_name in ("npc-drops.json", "subtables.json", "unresolved-items.json"):
        assert Path(
            config.DOCS_DROPS_PATH / file_name
        ).exists(), f"docs/drops-json/{file_name} must exist"

    npc_drops = _load("npc-drops.json")
    assert set(npc_drops) == {"meta", "tables", "npcs"}
    assert npc_drops["meta"]["table_count"] == len(npc_drops["tables"])
    assert npc_drops["meta"]["npc_count"] == len(npc_drops["npcs"])
    assert isinstance(_load("unresolved-items.json"), list)


def test_drops_schema_validation():
    """Validate every drop table in npc-drops.json against schema."""
    # Read in the drops schema file
    path_to_schema = Path(config.DATA_SCHEMAS_PATH / "schema-drops.json")
    with open(path_to_schema, "r", encoding="utf-8") as f:
        schema = json.loads(f.read())

    # Validator object with schema attached
    v = validator.MyValidator(schema)

    # Validate each drop table in the dump
    for table_id, table in _load("npc-drops.json")["tables"].items():
        assert v.validate(table), (
            f"Schema validation failed for drop table: {table_id}. "
            f"Errors: {v.errors}"
        )


def test_npcs_reference_known_tables():
    """Every NPC points at drop tables that exist in the same file."""
    npc_drops = _load("npc-drops.json")
    tables = npc_drops["tables"]

    for npc_id, npc in npc_drops["npcs"].items():
        assert npc["npc_id"] == int(npc_id)
        if not npc["tables"]:
            assert int(npc_id) in {8058, 8060, 13686}, f"unexpected empty NPC {npc_id}"
        for table_id in npc["tables"]:
            assert (
                table_id in tables
            ), f"npc {npc_id} references unknown table {table_id}"
    assert {
        int(npc_id) for npc_id, npc in npc_drops["npcs"].items() if not npc["tables"]
    } == {8058, 8060, 13686}


def test_commented_source_quantities_are_executable():
    """Invisible editor notes must not turn guaranteed drops into raw expressions."""
    tables = _load("npc-drops.json")["tables"]
    for table_id in ("hydra", "colossal_hydra", "bloodthirsty_hydra"):
        bones = next(
            entry
            for entry in tables[table_id]["entries"]
            if entry.get("item_id") == 22786 and entry.get("always")
        )
        assert bones["quantity"] == [1, 1], table_id
        assert "quantity_raw" not in bones
    scales = [
        entry for entry in tables["zulrah"]["entries"] if entry.get("item_id") == 12934
    ]
    assert next(entry for entry in scales if entry.get("always"))["quantity"] == [
        100,
        299,
    ]
    assert next(entry for entry in scales if not entry.get("always"))["quantity"] == [
        500,
        500,
    ]


def test_explicit_inline_drop_conditions_survive_export():
    """Real inline conditions use ungrouped references and groups other than d."""
    tables = _load("npc-drops.json")["tables"]
    cases = (
        ("animated_bronze_armour", "Combat Achievements"),
        ("ancient_feral_vyre", "bloodmoon"),
        ("brutal_blue_dragon", "Ruins of Tapoyauik"),
        ("moss_giant", "1/75"),
        ("moss_giant", "off-task in the Wilderness"),
    )
    for table_id, condition in cases:
        notes = [
            note
            for section in ("entries", "tertiary")
            for entry in tables[table_id].get(section, [])
            for note in entry.get("notes", [])
        ]
        assert any(condition in note for note in notes), table_id


def test_corpus_quantity_alternatives_export_executable_defaults():
    """Known alternatives export their first quantity, every alternative and the source rule."""
    tables = _load("npc-drops.json")["tables"]
    cases = (
        (
            "duke_sucellus",
            "Bronze chainbody",
            "11,17",
            [[11, 11], [17, 17]],
            "perfect_kill",
        ),
        ("the_whisperer", "Coal", "303,455", [[303, 303], [455, 455]], "perfect_kill"),
        ("crystalline_bat", "Raw paddlefish", "1,3", [[1, 1], [3, 3]], None),
    )
    for table_id, name, raw, alternatives, condition in cases:
        entry = next(
            entry for entry in tables[table_id]["entries"] if entry.get("name") == name
        )
        assert entry["quantity_raw"] == raw, table_id
        assert entry["quantity"] == alternatives[0], table_id
        assert [
            alt["quantity"] for alt in entry["quantity_alternatives"]
        ] == alternatives
        if condition:
            assert entry["quantity_selection"] == "conditional", table_id
            assert entry["quantity_alternatives"][1]["condition"] == {"type": condition}
        else:
            assert entry["quantity_selection"] == "unknown", table_id
            assert "condition" not in entry["quantity_alternatives"][1], table_id
    nails = next(
        entry
        for entry in tables["narwhal"]["entries"]
        if entry.get("name") == "Dragon nails"
    )
    assert nails["quantity_raw"] == "3-7,5-10"
    assert nails["quantity"] == [3, 7]
    assert nails["quantity_alternatives"][1] == {
        "quantity": [5, 10],
        "condition": {"type": "bounty_task", "monster": "narwhal"},
    }
    assert any("bounty task" in note for note in nails.get("notes", []))


def test_corpus_every_quantity_resolves_and_alternatives_are_accounted_for():
    """No row falls back to an unparsed quantity; the 116 alternative rows are typed."""
    tables = _load("npc-drops.json")["tables"]
    rows = [
        entry
        for table in tables.values()
        for section in ("entries", "tertiary")
        for entry in table.get(section, [])
    ]
    assert not [
        entry for entry in rows if "quantity_raw" in entry and "quantity" not in entry
    ]
    alternatives = [entry for entry in rows if "quantity_alternatives" in entry]
    assert len(alternatives) == 116
    kinds = {}
    for entry in alternatives:
        if entry["quantity_selection"] == "unknown":
            kind = "unknown"
        else:
            kind = entry["quantity_alternatives"][1]["condition"]["type"]
        kinds[kind] = kinds.get(kind, 0) + 1
    assert kinds == {
        "perfect_kill": 99,
        "bounty_task": 2,
        "preferred_method": 3,
        "unknown": 12,
    }


def test_corpus_dropped_together_pairs_are_single_slots():
    """Footnoted pairs export as one slot with bonus drops; their pools follow."""
    tables = _load("npc-drops.json")["tables"]

    def pairs(table):
        return sorted(
            (entry["item_id"], bonus["item_id"])
            for entry in table["entries"]
            for bonus in entry.get("bonus_drops", [])
        )

    expected = {
        "nex": ([(385, 2434), (6685, 3024)], 12),
        "commander_zilyana": ([(163, 3042), (6687, 3024)], 1524),
        "kril_tsutsaroth": ([(145, 157), (3026, 189)], 1524),
        "kreearra": ([(169, 163)], 1524),
        "general_graardor": ([], 1524),
        "ammonite_crab": ([(21543, 21545)], 128),
        "chaos_fanatic": ([(1035, 1033)], 133),
        "ancient_zygomite": ([(21545, 21543)], 118),
        "scavenger_beast": ([], 18),
    }
    for table_id, (table_pairs, max_roll) in expected.items():
        table = tables[table_id]
        assert pairs(table) == table_pairs, table_id
        assert table["main_max_roll"] == max_roll, table_id
        partners = {partner for _, partner in table_pairs}
        assert not [
            entry for entry in table["entries"] if entry.get("item_id") in partners
        ]


def test_shared_tables_are_exported():
    """Every shared table a drop table rolls into is defined in subtables.json."""
    npc_drops = _load("npc-drops.json")
    subtables = _load("subtables.json")

    for table_id, table in npc_drops["tables"].items():
        for entry in table["entries"]:
            shared_table = entry.get("shared_table")
            # The empty key is a multi-roll herb table, which has no single
            # shared table to point at.
            if shared_table:
                assert (
                    shared_table in subtables
                ), f"drop table {table_id} rolls undefined shared table {shared_table}"


def test_shellbane_uses_current_page_without_stale_duplicate():
    drops = _load("npc-drops.json")
    npc = drops["npcs"]["14860"]
    assert npc["tables"] == ["shellbane_gryphon"]
    table = drops["tables"][npc["tables"][0]]
    assert table["wiki_page"] == "Shellbane gryphon"
    assert table["main_max_roll"] == 128
    assert "shellbane_gryphon_2" not in drops["tables"]
