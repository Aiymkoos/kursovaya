"""Естеліктер журналы (Tab): диалогта табылған детальдар."""


class Journal:
    def __init__(self, catalog):
        """catalog — {id: {"who": кейіпкер, "text": мәтін}} (JSON-нан)."""
        self.catalog = catalog
        self._ids = []

    def add(self, memory_id):
        """Жазба қосады; қайта қосылмайды. Жаңа болса True қайтарады."""
        if memory_id not in self.catalog:
            raise KeyError(f"Белгісіз естелік: {memory_id}")
        if memory_id in self._ids:
            return False
        self._ids.append(memory_id)
        return True

    def has(self, memory_id):
        return memory_id in self._ids

    def entries(self):
        return [(i, self.catalog[i]) for i in self._ids]

    def __len__(self):
        return len(self._ids)

    def to_list(self):
        return list(self._ids)

    @classmethod
    def from_list(cls, catalog, ids):
        j = cls(catalog)
        for i in ids:
            j.add(i)
        return j
