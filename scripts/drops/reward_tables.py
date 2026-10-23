"""Source-parsed reward tables, deliberately unbound from ordinary NPC kills."""

import re
from typing import Dict

from scripts.drops import drops_wikitext as wiki
from scripts.drops.drops_tables import ItemIdLookup, _parse_quantity


def _quantity_options(notes):
    for note in notes:
        match = re.search(r"Possible quantities:\s*([0-9][0-9,\s]*)", note, re.I)
        if match:
            values = [value.strip() for value in match.group(1).strip().split(",")]
            if values and all(value.isdigit() for value in values):
                return [int(value) for value in values]
    return None


def export_reward_tables(pages: Dict[str, str], items: ItemIdLookup) -> Dict:
    """Preserve reward variants and source semantics without assigning kill loot.

    Normal drop parsing does not opt into DropsLineReward. This separate export
    has no NPC mapping: domain consumers must explicitly select a reward table.
    Unknown IDs, quantities and rates remain visible rather than guessed.
    """
    tables = {}
    unparsed = {}
    for page, source in pages.items():
        if not source or "dropslinereward" not in source.lower():
            continue
        source_count = len(wiki.extract_templates(source, "DropsLineReward"))
        exported_count = 0
        for table in wiki.parse_all_drop_tables(source, include_rewards=True):
            if not any(drop.is_reward for drop in table.drops):
                continue
            exported_count += sum(drop.is_reward for drop in table.drops)
            label = table.drop_variant or table.table_name
            variant = re.sub(r"\s+drops$", "", label, flags=re.I)
            identity = page if variant.lower() == "drops" else page + " " + variant
            table_id = re.sub(r"[^a-z0-9]+", "_", identity.lower()).strip("_")
            entries = []
            for drop in table.drops:
                row = {
                    "item_id": items.resolve(drop.name),
                    "name": drop.name,
                    "section": drop.subsection,
                    "rarity_raw": drop.reward_source_rarity or drop.rarity,
                    "source_template": (
                        "DropsLineReward" if drop.is_reward else "DropsLine"
                    ),
                }
                quantity = _parse_quantity(drop.quantity)
                if quantity is None:
                    row["quantity_raw"] = drop.quantity
                else:
                    row["quantity"] = quantity
                if drop.alternate_rarity:
                    row["alternate_rarity_raw"] = drop.alternate_rarity
                if drop.assumed_rarity:
                    row["assumed_rarity"] = True
                if (
                    drop.reward_source_rarity
                    and drop.reward_source_rarity != drop.rarity
                ):
                    row["resolved_rarity"] = drop.rarity
                if drop.is_noted:
                    row["noted"] = True
                if drop.notes:
                    row["notes"] = drop.notes
                options = _quantity_options(drop.notes)
                if options is not None:
                    row["quantity_options"] = options
                entries.append(row)
            if table_id in tables:
                raise ValueError("Duplicate reward table identifier: " + table_id)
            tables[table_id] = {
                "wiki_page": page.replace("_", " "),
                "label": table.drop_variant or table.table_name,
                "entries": entries,
            }
        if source_count != exported_count:
            unparsed[page] = {
                "source_rows": source_count,
                "exported_rows": exported_count,
            }
    return {"schema_version": 1, "tables": tables, "unparsed_reward_rows": unparsed}
