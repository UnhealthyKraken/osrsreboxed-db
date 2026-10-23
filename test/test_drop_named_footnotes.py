"""A named footnote reference can appear before its definition."""

import pytest

from scripts.drops import drops_wikitext


@pytest.mark.parametrize("field", ["namenotes", "raritynotes"])
def test_self_closing_reference_does_not_consume_its_later_definition(field):
    note = "Coins are only dropped on a bounty task."
    body = (
        "{{DropsLine|name=Coins|quantity=2|rarity=1/2|"
        + field
        + '=<ref name="coins" group="d" />}}\n'
        + '<ref name="coins" group="d">'
        + note
        + "</ref>"
    )
    assert drops_wikitext.collect_named_footnotes(body) == {"coins": note}
    source = "{{Infobox Monster|id=1}}\n==Drops==\n===Other===\n" + body
    drop = drops_wikitext.parse_all_drop_tables(source)[0].drops[0]
    assert drop.notes == [note]


@pytest.mark.parametrize(
    "attrs, accepted",
    [
        ('name="drop" group="d"', True),
        ("name='drop' group='d'", True),
        ('GROUP = D name="drop"', True),
        ('name="drop" group=d', True),
        ('name="drop" group="x"', False),
        ('name="drop" group="dungeon"', False),
        ('name="drop"', False),
        ('name="drop" data-group="d"', False),
        ('name="drop" grouper="d"', False),
        ('name="drop" title="example group=d other"', False),
    ],
)
def test_named_reference_definitions_and_links_use_exact_drop_group(attrs, accepted):
    note = "Only dropped on an active bounty task."
    definition = f"<ref {attrs}>{note}</ref>"
    assert drops_wikitext.collect_named_footnotes(definition) == (
        {"drop": note} if accepted else {}
    )
    assert drops_wikitext._resolve_named_ref_links(
        f"<ref {attrs} />", "", {"drop": note}
    ) == ([note] if accepted else [])


def test_other_reference_group_cannot_shadow_drop_group_with_same_name():
    body = (
        '<ref name="drop" group="x">Unrelated citation.</ref>'
        '<ref name="drop" group="d">Only on a bounty task.</ref>'
    )
    assert drops_wikitext.collect_named_footnotes(body) == {
        "drop": "Only on a bounty task."
    }
