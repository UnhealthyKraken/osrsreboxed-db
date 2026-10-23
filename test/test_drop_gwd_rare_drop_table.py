"""The God Wars bosses roll their own variant rare drop and gem tables."""

import json
import re
from pathlib import Path

import pytest

from osrsreboxed import items_api
from scripts.drops import drops_tables
from scripts.drops import drops_wikitext as drops

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "data/monsters/monsters-wiki-page-text.json"
SHARED_CACHE = ROOT / "data/drops/drop-tables-wiki-page-text.json"

GWD_BOSSES = {
    "Commander Zilyana": 129,
    "General Graardor": 129,
    "K'ril Tsutsaroth": 130,
    "Kree'arra": 129,
}
GWD_KEYS = ["gwdRareDrop", "gwdGem"]


@pytest.fixture(scope="module")
def pages():
    return json.loads(CORPUS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def shared_pages():
    return json.loads(SHARED_CACHE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def real_items():
    return drops_tables.ItemIdLookup(items_api.load())


def gwd_accesses(table):
    return [
        (a.table_key, a.numerator, a.denominator)
        for a in table.subtable_accesses
        if a.table_key.startswith("gwd")
    ]


def test_only_the_four_god_wars_bosses_use_the_template(pages):
    users = {title for title, text in pages.items() if text and "{{GWDRDT}}" in text}
    assert users == set(GWD_BOSSES)


@pytest.mark.parametrize("title", sorted(GWD_BOSSES))
def test_god_wars_pages_roll_both_variant_tables(pages, title):
    tables = drops.parse_all_drop_tables(pages[title])
    accesses = [gwd_accesses(table) for table in tables]
    assert [("gwdRareDrop", 8, 127), ("gwdGem", 2, 127)] in accesses
    # The regular tables are not rolled: the variant replaces them.
    for table in tables:
        assert not {a.table_key for a in table.subtable_accesses} & {"rareDrop", "gem"}


def test_pages_without_the_template_roll_no_variant_table(pages):
    for title in ("Abyssal demon", "Hellhound", "Nex"):
        for table in drops.parse_all_drop_tables(pages[title]):
            assert gwd_accesses(table) == []


@pytest.mark.parametrize("title,used", sorted(GWD_BOSSES.items()))
def test_god_wars_pools_count_the_variant_accesses(pages, real_items, title, used):
    table = next(
        t for t in drops.parse_all_drop_tables(pages[title]) if gwd_accesses(t)
    )
    exported = drops_tables.build_table_json(
        drops_tables.build_table_spec(title.replace(" ", "_"), table, real_items)
    )
    pool = [
        e
        for e in exported["entries"]
        if (e.get("out_of") == exported["main_max_roll"] or e.get("shared_table"))
        and not e.get("always")
        and not e.get("separate_roll")
        and not e.get("pre_roll")
    ]
    assert sum(e["weight"] for e in pool) == used
    # The page's coin rows already include the variant tables' coin outcomes,
    # so the pool exceeds 127 and the denominator follows it.
    assert exported["main_max_roll"] == used
    shared = [
        (e["shared_table"], e["weight"], e["out_of"])
        for e in pool
        if e.get("shared_table")
    ]
    assert shared == [("gwdRareDrop", 8, 127), ("gwdGem", 2, 127)]


def test_cached_variant_page_states_the_template_access_rates(shared_pages):
    text = shared_pages[drops_tables.GWD_SHARED_TABLE_PAGE]
    assert "The chance to access the GWDRDT is 8/127" in text
    assert "The chance to access the GWDGDT is 2/127" in text
    assert [
        (key, numerator, denominator)
        for key, numerator, denominator in drops.GWDRDT_ACCESSES
    ] == [("gwdRareDrop", 8, 127), ("gwdGem", 2, 127)]


def test_variant_tables_export_from_their_own_page(shared_pages, real_items):
    subtables = drops_tables.export_shared_subtables(shared_pages, real_items)
    for key in ("gwdRareDrop", "gwdGem", "gwdMegaRare"):
        table = subtables[key]
        assert table["wiki_page"] == drops_tables.GWD_SHARED_TABLE_PAGE
        rates = [
            re.fullmatch(r"(\d+)/(\d+)", e["rarity_raw"]) for e in table["entries"]
        ]
        assert all(rates), key
        assert {int(r.group(2)) for r in rates} == {128}, key
        assert sum(int(r.group(1)) for r in rates) == 128, key
        assert all(
            e.get("shared_table") or isinstance(e.get("item_id"), int)
            for e in table["entries"]
        ), key
    refs = {
        key: [
            e["shared_table"]
            for e in subtables[key]["entries"]
            if e.get("shared_table")
        ]
        for key in ("gwdRareDrop", "gwdGem", "gwdMegaRare")
    }
    assert refs == {
        "gwdRareDrop": ["gwdGem", "gwdMegaRare"],
        "gwdGem": ["gwdMegaRare"],
        "gwdMegaRare": [],
    }
    names = {e.get("name") for e in subtables["gwdRareDrop"]["entries"]}
    assert "Rune sword" in names and "Runite bar" not in names
    # The regular tables still come from the shared Drop table page.
    assert subtables["rareDrop"]["wiki_page"] == drops_tables.SHARED_TABLE_PAGE
    assert "Runite bar" in {e.get("name") for e in subtables["rareDrop"]["entries"]}
