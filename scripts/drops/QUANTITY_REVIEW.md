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

## God Wars rare drop tables (`{{GWDRDT}}`)

General Graardor, Commander Zilyana, K'ril Tsutsaroth and Kree'arra write `{{GWDRDT}}` under `===Rare drop table===`. The template takes no arguments. It expands to "an 8/127 chance of rolling the God Wars Dungeon-variant rare drop table and a 2/127 chance of rolling the God Wars Dungeon-variant gem drop table", citing Mod Ash ("2/127 to go to gems OR 8/127 to go to RDT, from where 20/128 goes to gems").

Those are not the regular shared tables:
- The page [God Wars Dungeon-variant rare drop table](https://oldschool.runescape.wiki/w/God_Wars_Dungeon-variant_rare_drop_table) has its own rare drop, gem and mega-rare tables (each /128).
- A rune sword replaces the runite bar, and some quantities differ.
- Coins fill the regular table's empty share.
- The ring of wealth has no effect (also cited from Mod Ash).

What the exporter does now:
- `_parse_subtable_accesses` emits `gwdRareDrop` 8/127 and `gwdGem` 2/127 for the template, from `GWDRDT_ACCESSES`.
- `export_shared_subtables` reads the three variant tables (`gwdRareDrop`, `gwdGem`, `gwdMegaRare`) from that page.
- The page is now cached beside `Drop table` in `data/drops/drop-tables-wiki-page-text.json`. A test pins the 8/127 and 2/127 statements in the cached text to the constant.

**The pools exceed 127, recorded rather than patched:**

| Boss | Pool rows + 8 + 2 | Previously used | Coin row on the page |
|---|---|---|---|
| Commander Zilyana | 129 | 119 | 31.2/127 |
| General Graardor | 129 | 119 | 31.7/127 + 1.25/127 |
| K'ril Tsutsaroth | 130 | 120 | 36.7/127 |
| Kree'arra | 129 | 119 | 43.7/127 + 1.25/127 |

- Each page's coin footnote says its coins "come from rolls on … GDT and RDT". So the page's coin rate already includes the variant tables' coin outcomes, which the export now also rolls through those tables. Coins are therefore counted twice, by roughly the tables' coin share.
- The exporter also truncates the fractional coin rates (31.2 becomes 31).
- K'ril's page sums one slot higher than the other three.
- No published figure separates the main-table coin weight. So the existing rule applies, and `main_max_roll` follows the used total (129/130/129/129). Each other pool row moves from x/127 to x/129 (x/130 for K'ril), and the access rows keep their source 8/127 and 2/127.

Verification:
- `test/test_drop_gwd_rare_drop_table.py`: 12 red-first tests on the real corpus and cache pages. The pool pins in `test_drop_bonus_drops.py` and `test_drops_database.py` move to 129/130/129/129. The full suite is 338 passed, plus the same pre-existing `test_dialogue_hooks.py::test_generated_exports` failure.
- Two complete regenerations are byte-identical. `npc-drops.json` SHA-256 is `38e7059c26af8cb09cc086d10476b45ff65122cd3f3ff1bd3ee64dc8da065651`, and `subtables.json` SHA-256 is `355f429aaa102fc119467c545e1ea492cd6d2b8cc42e58c568e22eafc6f2b47f`.
- Against the previous export (`983bc65d…`), only these changed:
  - The four boss tables: two access rows added, `main_max_roll`, and the pool rows' `out_of`/`rarity`.
  - `meta.shared_tables`, which gained `gwdGem` and `gwdRareDrop`.
  - `subtables.json`, which gained the three variant tables. The existing shared tables are unchanged.
- No other table, NPC mapping or tertiary row changed. `reward-tables.json` and `unresolved-items.json` are identical.

## Still open (findings, not patched here)

- No consumer can yet tell a perfect kill, an active bounty task or the Chasm preferred method, so the first-listed amount applies until those mechanics exist.
- The God Wars coin rows count the variant tables' coins a second time, and the four pools sum to 129/130/129/129 of a published 127 (see above).
- Maggot King's "drop together" footnote sits in the take-eggs table, whose rows the parser loses; that NPC maps to an empty table.
- Chaos Fanatic's emerald/sapphire pair is written "dropped alongside" and is not bundled.
- Earlier gates remain: 165 assumed rates, five unresolved herb batches and incomplete quest/location conditions.
