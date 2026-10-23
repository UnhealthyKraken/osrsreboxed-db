"""Only references whose actual group attribute is d are drop footnotes."""

import pytest

from scripts.drops import drops_wikitext

DROP_ATTRIBUTES = [
    'name="drop" group="d"',
    "name='drop' group='d'",
    'name="drop" group=d',
    'name="drop" GROUP = "D"',
    'name="drop"\tgroup\t=\tD',
    'name="drop" data-group="x" group="d"',
]
OTHER_ATTRIBUTES = [
    'name="drop" group="x"',
    'name="drop" group="dd"',
    'name="drop" group="dropped"',
    'name="drop" group="d-x"',
    'name="drop" data-group="d"',
    'name="drop" subgroup="d"',
    'name="drop" groupish="d"',
    'name="drop" title="group=d"',
    'name="drop" group="x" title="group=d"',
]
NOTE = "Coins are only dropped on a bounty task."


@pytest.mark.parametrize("attrs", DROP_ATTRIBUTES + OTHER_ATTRIBUTES)
def test_collector_checks_the_actual_reference_group(attrs):
    actual = drops_wikitext.collect_named_footnotes(f"<ref {attrs}>{NOTE}</ref>")
    assert actual == ({"drop": NOTE} if attrs in DROP_ATTRIBUTES else {})


@pytest.mark.parametrize("attrs", DROP_ATTRIBUTES + OTHER_ATTRIBUTES)
def test_resolver_checks_the_actual_reference_group(attrs):
    actual = drops_wikitext._resolve_named_ref_links(
        f"<ref {attrs} />", "", {"drop": NOTE}
    )
    assert actual == ([NOTE] if attrs in DROP_ATTRIBUTES else [])


def parse_reference(definition_attrs, reference_attrs, note):
    body = (
        "{{Infobox Monster|id=1}}\n==Drops==\n===Other===\n"
        "{{DropsLine|name=Coins|quantity=2|rarity=1/2|raritynotes="
        f"<ref {reference_attrs} />"
        "}}\n"
        f"<ref {definition_attrs}>{note}</ref>"
    )
    return drops_wikitext.parse_all_drop_tables(body)[0].drops


@pytest.mark.parametrize("attrs", DROP_ATTRIBUTES + OTHER_ATTRIBUTES)
def test_non_drop_references_cannot_filter_coins_as_free_to_play_only(attrs):
    drops = parse_reference(attrs, attrs, "Only dropped in free-to-play.")
    if attrs in DROP_ATTRIBUTES:
        assert drops == []
    else:
        assert len(drops) == 1
        assert drops[0].name == "Coins"
        assert drops[0].notes == []


@pytest.mark.parametrize("attrs", OTHER_ATTRIBUTES)
def test_full_parser_keeps_reference_groups_isolated(attrs):
    drops = parse_reference('name="drop" group="d"', attrs, NOTE)
    assert len(drops) == 1
    assert drops[0].notes == []


@pytest.mark.parametrize("attrs", DROP_ATTRIBUTES + OTHER_ATTRIBUTES)
def test_inline_reference_bodies_only_apply_for_the_actual_drop_group(attrs):
    note = "Only dropped in free-to-play."
    assert drops_wikitext.parse_inline_note_fields(f"<ref {attrs}>{note}</ref>") == (
        [note] if attrs in DROP_ATTRIBUTES else []
    )
    body = (
        "{{Infobox Monster|id=1}}\n==Drops==\n===Other===\n"
        "{{DropsLine|name=Coins|quantity=2|rarity=1/2|raritynotes="
        f"<ref {attrs}>{note}</ref>"
        "}}"
    )
    drops = drops_wikitext.parse_all_drop_tables(body)[0].drops
    assert len(drops) == (0 if attrs in DROP_ATTRIBUTES else 1)


def test_inline_plain_notes_survive_removing_non_drop_reference_bodies():
    assert drops_wikitext.parse_inline_note_fields(
        'Only dropped on a bounty task. <ref name="drop" group="x">'
        "Only dropped in free-to-play.</ref>"
    ) == ["Only dropped on a bounty task."]
