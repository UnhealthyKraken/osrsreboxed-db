# Quantity alternatives and dropped-together pairs: export contract

The Wiki's [DropsLine contract](https://oldschool.runescape.wiki/w/Template:DropsLine/doc) defines commas as separators between distinct quantities, never thousands separators. Earlier exports concatenated the digits (`1500,2250` became 1,502,250) and a later candidate kept them only as `quantity_raw`, which consumers fell back to 1 for. Branch `fix/conditional-quantities-and-bundles` closes both.

## What the export now says

- `quantity`: the first-listed alternative, the source's default.
- `quantity_alternatives`: every listed alternative in source order, `{"quantity": [min, max]}`, with a typed `condition` on later alternatives only where the source states the rule.
- `quantity_selection`: `"conditional"` when the second alternative has a typed condition; `"unknown"` when the source publishes no rule.
- `quantity_raw`: retained as provenance whenever alternatives exist. A token with a leading zero (`1,000`) is not a quantity the template allows, so such a field stays raw with no `quantity`.
- `noted` stays a row property: no corpus row writes `(noted)` on a non-final alternative without the final one.
- `bonus_drops`: exactly two adjacent main-table rows in one subsection, at the same rate, sharing a named group-d footnote whose body says they are dropped together, export as one slot; the second row becomes the first row's bonus drop and the pool denominator follows.

## Condition rules (closed set, one source rule each)

| condition | source rule | rows |
|---|---|---|
| `perfect_kill` | the page states "defeating the boss perfectly will earn 50% more loot from the standard drop table" (Mod Ayiza, cited) and the row is a main-table row with exactly two non-decreasing alternatives | 99 (Vardorvis 25, The Leviathan 25, The Whisperer 25, Duke Sucellus 24) |
| `bounty_task` + `monster` | the row's **quantity** note says "while on a(n) <monster> bounty task"; the same phrase in a rarity note does not count | 2 (Narwhal, Orca) |
| `preferred_method` + `location` | a note says "killed with preferred method in the Chasm of Fire" | 3 (Lesser, Greater, Black demon ashes) |

The other 12 alternative rows (Drake and Guardian Drake shark lures `8;10;12`, Skeleton air runes `12,15`, three Crystalline Gauntlet paddlefish `1,3`, six Ent log rows) have no published distribution and are `unknown`. Consumers must treat any choice among them as an assumption.

## Dropped-together pairs

Bundled: Nex (sharks + prayer potions, brews + restores; pool 14 to 12), Commander Zilyana (2 pairs; pool 133 to 127), K'ril Tsutsaroth (2 pairs; 136 to 127), Kree'arra (1 pair), Ammonite Crab (129 to 128), Chaos Fanatic (robes; 137 to 133), Ancient Zygomite. Left as separate slots by the rule: Scavenger beast's three secondary ingredients (a three-row run whose rows sum the table to exactly 18).

## Verification

- 168 focused drop tests, including red-first corpus guards for every rule and number above; full suite 326 passed with one pre-existing unrelated failure (`test_dialogue_hooks.py::test_generated_exports`, While Guthix Sleeps fingerprint).
- Two complete regenerations are byte-identical: `npc-drops.json` SHA-256 `983bc65d3b046ee37d45e108ce8c678cb755cc628678cc4eb3a6d1323bbfd406`; `subtables.json` unchanged.
- Against an export of the branch base (`2d2965fb`, SHA-256 `94f3c6e3…`) the only differences are the 116 quantity rows and the seven bundled tables: no note, rate, mapping, table or shared-table change.

## Still open (findings, not patched here)

- No consumer can yet tell a perfect kill, an active bounty task or the Chasm preferred method, so the first-listed amount applies until those mechanics exist.
- `{{GWDRDT}}` (the God Wars rare-drop-table access, 8/127) is not parsed, so the four God Wars pools use 119 or 120 of 127 slots.
- Maggot King's "drop together" footnote sits in the take-eggs table, whose rows the parser loses; that NPC maps to an empty table.
- Chaos Fanatic's emerald/sapphire pair is written "dropped alongside" and is not bundled.
- Earlier gates remain: 165 assumed rates, five unresolved herb batches and incomplete quest/location conditions.
