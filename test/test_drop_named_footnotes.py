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
