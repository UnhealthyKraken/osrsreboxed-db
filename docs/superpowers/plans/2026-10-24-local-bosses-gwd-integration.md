# Local Bosses and God Wars Source Integration Plan

**Goal:** Provide a safe canonical merge candidate and complete deterministic exports for local game integration.
**Architecture:** Start from the preserved local source tip 7ff4b112, port reviewed PR14/15 parser fixes, retain every local-only source/reward exporter, and regenerate every drop output from cached inputs. Do not modify the primary checkout, TSPS, or Claude-owned clue worktrees.
**Tech Stack:** Python source pipeline, pytest, cached Wiki source, JSON schema.
**Spec:** Coordinating agent request to integrate reviewed boss/GWD fixes while preserving local authoring work.

- [x] Inspect AGENTS/CLAUDE, record preserved refs, create local/bosses-gwd-integration in existing isolated checkout.
- [x] Generate complete pre-integration local baseline into parent .runtime/local-bosses-gwd/baseline.
- [x] Reconcile source/tests using reviewed PR14/15 changes without replacing local-only parser/reward features.
- [x] Run relevant regressions and source suite; retain known unrelated failures as evidence.
- [x] Generate full output twice; verify every output byte and classify all semantic changes against baseline/public export.
- [x] Commit source and regenerated artifact candidate, report exact hashes and integration scope.

## Review focus

Retain named-reference grouping, quest catalogue conditions, variable herb rolls, separate reward-table and local clue exports. Preserve exact pre-rolls, Nex pairs, Mimic reward ownership, Bandit quest ownership and empty quest IDs 8058/8060/13686. God Wars rates use exact 1524-slot exclusive pools. Generated JSON is never patched or hand merged.

## Final source and artifact evidence

Preserved refs: primary `fix/gwd-rare-drop-table` at `7ff4b1128a95664aa38b6398ba1020317627d3e0`; public quantity branch `fed6d8825823b2a538ed1ae30fb185f519d64be2`; public GWD branch `1bbeae141e88bca3d524e71fc712706fb7de084f`. The candidate is based on the original local tip; source fixes are ported from reviewed commits `5493e563` and `1f5eea57` without merging broad public ancestry or touching either clue worktree.

The source port retains local named-reference grouping, nested quantity notes, quest-title catalogue, variable herb-roll metadata, separate reward tables and clue exporters. Quantity notes remain source conditions; an activity is never invented as a quest. Because this local contract is broader than public PR #14, bundle eligibility compares quantity notes as well as name/rate notes. A new source test reproduced the lost partner bounty requirement before the guard and passes afterward.

Independent review found an additional pre-existing serializer bypass: mixed-denominator pre-rolls used generic separate-roll serialization. Both pre-roll branches now use the exact serializer; ordinary separate rolls retain their original path. Source tests reproduced `1/181.1` rounding and executable invalid `1/0` / `351/350`, then verified exact `10/1811`, preserved integer `4/540` and raw-only invalid probabilities. This correction changes no row in the checked-in cache corpus.

Fresh verification: **381 passed, one pre-existing failure**, `test/test_dialogue_hooks.py::test_generated_exports`, While Guthix Sleeps fingerprint (`64e6b0...` actual vs `e72f3e...` audited). Dialogue source and artifacts are untouched. The exact/bundle/GWD focused run passes **109 tests**; final copied generated-doc schema/corpus checks pass **9/9**. Independent review and incremental serializer re-review are clear.

Two complete cached-input exports, parent `.runtime/local-bosses-gwd/final-a` and `final-b`, contain all four output files and match byte-for-byte. They were copied verbatim into `docs/drops-json/`; no generated JSON was patched or merged. The pre-integration source baseline matches the original tracked table/mapping data; its metadata date advances from 2026-10-23 to 2026-10-24. Windows working-output hashes include the generator's native line endings.

| Output | SHA-256 |
|---|---|
|npc-drops.json|`f47f58079fff12b75d082111f6d6096b1abb0e8a4a4c9a05f99f1407502d2c44`|
|reward-tables.json|`1738067712a74559967873322e030a9730ebd9b20be1000f0ed7c28a68027774`|
|subtables.json|`355f429aaa102fc119467c545e1ea492cd6d2b8cc42e58c568e22eafc6f2b47f`|
|unresolved-items.json|`7abbfe34cb6e64fe38b75cba18e76ae14acacb1f7e678e21a30e838f4268537c`|

## Complete semantic delta against the preserved local export

- All **3,089 existing NPC records are identical**. Added empty-table quest records **8058, 8060 and 13686** produce **3,092** records; all **1,112** table identities and **3,119** table references remain.
- Four GWD generals change from approximate 127-slot/separate-unique models to one exact **1524-slot** pool. Normal coin weights are **330 / 336 / 396 / 480** for Zilyana / Graardor / K'ril / Kree. Graardor/Kree unique Coins retain exact **15/1524**. Shared accesses retain **96/1524** and **24/1524**; source fractions survive in `published_rarity`. All source quantities, alternatives, notes and paired supplies are preserved.
- **12 Hydra-part pre-roll rows in four tables** (`alchemical_hydra`, `bloodthirsty_hydra`, `colossal_hydra`, `hydra`) serialize exact fractional source rates. Only weight/denominator/derived rarity change; item quantities, notes and flags are identical.
- Every other table and every non-pre-roll portion of the four Hydra tables is identical. Nex pairs, Mimic reward ownership, Bandit champion quest notes, and exact Thermy pre-roll metadata are preserved.
- **Every shared subtable**, the separate reward-table export and unresolved output are byte-identical to the regenerated local baseline. `reward-tables.json` was previously generated by local source but untracked; this candidate includes the complete generated output.
- Compared with public PR #15 there are no mapping differences; 294 table differences and the regular seed table reflect retained local-only parsing behavior. They are not additional changes introduced here: the complete local-baseline comparison permits only the eight tables above.

Machine evidence is in parent `.runtime/local-bosses-gwd/comparison-final.json` and `public-comparison.json`; the verifier checks every mapping/table and every complete output. Source/test logs use the same directory. No upstream publication, primary-checkout switch, TSPS modification, game launch, deployment or restart was performed.
