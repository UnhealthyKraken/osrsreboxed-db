"""Keep unsupported Wiki quantity alternatives distinct from numeric ranges."""

from types import SimpleNamespace

import pytest

from scripts.drops import drops_tables, drops_wikitext


def export_quantity(raw):
    lookup = drops_tables.ItemIdLookup(
        [
            SimpleNamespace(
                id=995,
                name="Coins",
                wiki_name="Coins",
                tradeable_on_ge=True,
                duplicate=False,
                noted=False,
                placeholder=False,
                stacked=None,
            )
        ]
    )
    source = (
        "{{Infobox Monster|id=123}}\n==Drops==\n===100%===\n"
        "{{DropsTableHead}}\n"
        "{{DropsLine|name=Coins|quantity=" + raw + "|rarity=Always}}\n"
        "{{DropsTableBottom}}"
    )
    parsed = drops_wikitext.parse_all_drop_tables(source)[0]
    return drops_tables.build_table_json(
        drops_tables.build_table_spec("Test", parsed, lookup)
    )["entries"][0]


# Template:DropsLine/doc defines commas as separate quantities, never thousands:
# https://oldschool.runescape.wiki/w/Template:DropsLine/doc
@pytest.mark.parametrize(
    "raw, expected, noted",
    [
        ("1,3", "1,3", False),
        ("303,455", "303,455", False),
        ("200,300", "200,300", False),
        ("1,000", "1,000", False),
        ("3-7,5-10", "3-7,5-10", False),
        ("8;10;12", "8;10;12", False),
        ("280; 420", "280; 420", False),
        ("1,3;5-7", "1,3;5-7", False),
        ("200,300 (noted)", "200,300", True),
        ("1,<!-- editor note -->3", "1,3", False),
    ],
)
def test_quantity_alternatives_remain_raw_in_export(raw, expected, noted):
    entry = export_quantity(raw)
    assert entry["item_id"] == 995
    assert "quantity" not in entry
    assert entry["quantity_raw"] == expected
    assert entry.get("noted", False) is noted


@pytest.mark.parametrize(
    "raw, expected, noted",
    [
        ("1000", [1000, 1000], False),
        ("3-5", [3, 5], False),
        ("3 – 5", [3, 5], False),
        ("100-200 (noted)", [100, 200], True),
        ("1<!-- Hydra editor note -->", [1, 1], False),
        ("100-299<!-- separate 500 drop -->", [100, 299], False),
    ],
)
def test_plain_quantities_ranges_and_noted_comments_remain_numeric(
    raw, expected, noted
):
    entry = export_quantity(raw)
    assert entry["quantity"] == expected
    assert "quantity_raw" not in entry
    assert entry.get("noted", False) is noted
