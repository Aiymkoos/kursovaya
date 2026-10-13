"""Ойыншы таңдауларының флагтары: диалог пен жекпе-жекті байланыстырады."""


class Flags:
    def __init__(self, data=None):
        self._data = dict(data or {})

    def set(self, name, value=True):
        self._data[name] = value

    def get(self, name, default=False):
        return self._data.get(name, default)

    def check(self, requires):
        """requires — {флаг: күтілетін мән}; бәрі сәйкес болса True."""
        return all(self.get(k) == v for k, v in (requires or {}).items())

    def to_dict(self):
        return dict(self._data)

    @classmethod
    def from_dict(cls, data):
        return cls(data)
