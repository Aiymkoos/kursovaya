"""Ойыншының әрекеттерін жиілік кестесіне жазып, келесісін болжау (Марков тізбегі).

Күй — соңғы k әрекет (k = order). Кесте counts[күй][келесі әрекет].
Болжау: ең ұзын контексттен бастап (backoff) жиілігі бар алғашқысы алынады.
Сглаживание Лапласа: p = (n + a) / (N + a*|A|).
"""
from collections import defaultdict

ACTIONS = ("light", "heavy", "block")


class MarkovPredictor:
    def __init__(self, order=2, actions=ACTIONS, alpha=0.5):
        self.order = order
        self.actions = tuple(actions)
        self.alpha = alpha
        self.counts = defaultdict(lambda: defaultdict(int))  # контекст -> әрекет -> n
        self.history = []
        self.log = []   # (болжам, шын әрекет) жұптары — дәлдікті өлшеу үшін

    def _context(self, k):
        return tuple(self.history[-k:]) if k else ()

    def predict(self):
        """(әрекет, ықтималдық). Деректер жоқ болса (None, 0.0)."""
        for k in range(min(self.order, len(self.history)), -1, -1):
            table = self.counts.get(self._context(k))
            if not table:
                continue
            total = sum(table.values())
            denom = total + self.alpha * len(self.actions)
            probs = {a: (table.get(a, 0) + self.alpha) / denom for a in self.actions}
            best = max(self.actions, key=lambda a: (probs[a], -self.actions.index(a)))
            return best, probs[best]
        return None, 0.0

    def observe(self, action):
        """Шын әрекетті жазады; алдымен болжамның дұрыстығын журналға түсіреді."""
        pred, _ = self.predict()
        if pred is not None:
            self.log.append((pred, action))
        for k in range(0, self.order + 1):
            if k <= len(self.history):
                self.counts[self._context(k)][action] += 1
        self.history.append(action)

    @property
    def accuracy(self):
        if not self.log:
            return 0.0
        return sum(p == a for p, a in self.log) / len(self.log)

    def reset(self):
        self.counts.clear()
        self.history.clear()
        self.log.clear()
