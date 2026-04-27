# IndexedPO bundles a POFile with precomputed lookup indexes.
# Data container only -- no methods that modify PO content.

from collections import OrderedDict
from dataclasses import dataclass

import polib

from msg2po.conversion import build_occurrence_dict
from msg2po.po_utils import female_entries, translation_entries


@dataclass(frozen=True)
class IndexedPO:
    po: polib.POFile
    trans_map: dict
    female_map: dict[tuple[str, str], polib.POEntry]
    occ_dict: OrderedDict

    @classmethod
    def from_po(cls, po: polib.POFile) -> "IndexedPO":
        return cls(
            po=po,
            trans_map=translation_entries(po),
            female_map=female_entries(po),
            occ_dict=build_occurrence_dict(po),
        )
