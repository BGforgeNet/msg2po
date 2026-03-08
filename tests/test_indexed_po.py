# Tests for IndexedPO data container.

import polib
import pytest

from msg2po.indexed_po import IndexedPO
from msg2po.po_utils import CONTEXT_FEMALE


class TestIndexedPO:
    def _make_po(self):
        po = polib.POFile()
        male = polib.POEntry(msgid="Hello", msgstr="Bonjour", occurrences=[("dialog/1.msg", "100")])
        female = polib.POEntry(msgid="Hello", msgstr="Bonjour F", msgctxt=CONTEXT_FEMALE)
        po.append(male)
        po.append(female)
        return po

    def test_from_po_builds_trans_map(self):
        po = self._make_po()
        ipo = IndexedPO.from_po(po)
        assert "dialog/1.msg" in ipo.trans_map
        assert len(ipo.trans_map["dialog/1.msg"]) == 1

    def test_from_po_builds_female_map(self):
        po = self._make_po()
        ipo = IndexedPO.from_po(po)
        assert "Hello" in ipo.female_map
        assert ipo.female_map["Hello"].msgstr == "Bonjour F"

    def test_from_po_builds_occ_dict(self):
        po = self._make_po()
        ipo = IndexedPO.from_po(po)
        assert ("dialog/1.msg", "100") in ipo.occ_dict

    def test_with_rebuilt_indexes(self):
        po = self._make_po()
        ipo = IndexedPO.from_po(po)
        # Mutate the PO
        po.append(polib.POEntry(msgid="World", msgstr="Monde", occurrences=[("dialog/2.msg", "200")]))
        # Original indexes are stale
        assert "dialog/2.msg" not in ipo.trans_map
        # Rebuilt indexes reflect the mutation
        ipo2 = ipo.with_rebuilt_indexes()
        assert "dialog/2.msg" in ipo2.trans_map

    def test_po_reference_is_same_object(self):
        po = self._make_po()
        ipo = IndexedPO.from_po(po)
        assert ipo.po is po

    def test_frozen(self):
        po = self._make_po()
        ipo = IndexedPO.from_po(po)
        with pytest.raises(AttributeError):
            ipo.po = polib.POFile()  # type: ignore[misc]
