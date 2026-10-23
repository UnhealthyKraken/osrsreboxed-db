"""Quest gates must name cached quests; completion prose alone is not a quest."""

import json
from pathlib import Path

import pytest

from scripts.drops import drops_wikitext as drops


@pytest.mark.parametrize("depth", [2, 3, 4])
def test_delve_completion_is_retained_as_a_condition_not_a_quest(depth):
    note = f"Only dropped after completing delve level {depth} and deeper."
    assert drops.parse_quest_requirement(note) is None
    classified = drops.classify_note(note)
    assert classified.quest_requirements == []
    assert classified.condition == [note]


@pytest.mark.parametrize(
    "note, key, mode",
    [
        (
            "Only dropped during The Fremennik Trials.",
            "quest_fremenniktrials",
            "RequiresDuring",
        ),
        (
            "Only dropped during The Blood Moon Rises quest.",
            "quest_thebloodmoonrises",
            "RequiresDuring",
        ),
        (
            "Only dropped after completing Monkey Madness II.",
            "quest_monkeymadness2",
            "RequiresCompleted",
        ),
        (
            "Only dropped during the The Blood Moon Rises quest.",
            "quest_thebloodmoonrises",
            "RequiresDuring",
        ),
        (
            "Only dropped after completion of the Observatory quest.",
            "quest_observatoryquest",
            "RequiresCompleted",
        ),
        (
            "Only dropped during Underground Pass quest.",
            "quest_undergroundpass",
            "RequiresDuring",
        ),
        (
            "Only dropped if Family Crest isn't completed.",
            "quest_familycrest",
            "RequiresNotCompleted",
        ),
        (
            "Only dropped after completing Lunar Diplomacy after asking Meteora about her headgear.",
            "quest_lunardiplomacy",
            "RequiresCompleted",
        ),
    ],
)
def test_known_quest_names_are_canonicalized_without_swallowing_qualifiers(
    note, key, mode
):
    assert drops.parse_quest_requirement(note) == (
        f"WikiQuestDropRequirement(questKey={key}, mode={mode})"
    )
    assert drops.classify_note(note).condition == [note]


@pytest.mark.parametrize(
    "note",
    [
        "Only dropped after completing a Gauntlet run.",
        "Only dropped during an active bounty task.",
        "Only dropped after completing Watchtowering practice.",
    ],
)
def test_non_quest_activity_does_not_become_an_invented_quest_key(note):
    assert drops.parse_quest_requirement(note) is None
    assert drops.classify_note(note).condition == [note]


def test_cached_doom_demon_tear_keeps_delve_gate_without_inventing_a_quest():
    pages = json.loads(
        (
            Path(__file__).parents[1] / "data/monsters/monsters-wiki-page-text.json"
        ).read_text(encoding="utf-8")
    )
    tears = [
        drop
        for table in drops.parse_all_drop_tables(pages["Doom of Mokhaiotl"])
        for drop in table.drops
        if drop.name == "Demon tear"
    ]
    assert tears
    notes = " ".join(note for drop in tears for note in drop.notes)
    assert "delve level" in notes.lower()
    assert "quest_delve" not in notes
