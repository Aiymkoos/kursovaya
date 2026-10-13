"""Тестілеуге арналған «ойыншы-боттар»: әртүрлі ойын стильдері (эксперимент үшін)."""
import random

APPROACH = 95   # соғатын қашықтық


class Bot:
    """Базалық бот: жақындайды, стиль бойынша әрекет таңдайды."""

    name = "bot"

    def __init__(self, seed=1):
        self.rng = random.Random(seed)
        self.wait = self.rng.randint(10, 30)
        self.hold_left = 0

    def choose(self, fight, me, opp):
        raise NotImplementedError

    def decide(self, fight, me, opp):
        if self.hold_left > 0:
            self.hold_left -= 1
        hold = self.hold_left > 0
        if not me.can_act:
            return 0, None, hold
        toward = 1 if opp.x > me.x else -1
        if abs(opp.x - me.x) > APPROACH:
            return toward, None, hold
        cmd = self.choose(fight, me, opp)
        if cmd == "block":
            self.hold_left = 12
        return 0, cmd, self.hold_left > 0


class Aggressor(Bot):
    name = "aggressor"

    def choose(self, fight, me, opp):
        if self.wait > 0:
            self.wait -= 1
            return None
        self.wait = self.rng.randint(18, 40)
        return self.rng.choices(("light", "heavy", "block"), (0.65, 0.3, 0.05))[0]


class Pattern(Bot):
    """Қатаң қайталанатын әдет: L, L, H, B."""

    name = "pattern"
    SEQ = ("light", "light", "heavy", "block")

    def __init__(self, seed=1):
        super().__init__(seed)
        self.i = 0

    def choose(self, fight, me, opp):
        if self.wait > 0:
            self.wait -= 1
            return None
        self.wait = 24
        cmd = self.SEQ[self.i % len(self.SEQ)]
        self.i += 1
        return cmd


class RandomBot(Bot):
    name = "random"

    def choose(self, fight, me, opp):
        if self.wait > 0:
            self.wait -= 1
            return None
        self.wait = self.rng.randint(18, 40)
        return self.rng.choice(("light", "heavy", "block"))


class Reactive(Bot):
    """Қарсыластың дайындық қимылына жауап береді (парирлеуге тырысады), кейін соғады."""

    name = "reactive"

    def __init__(self, seed=1, jitter=(0, 5)):
        super().__init__(seed)
        self.jitter = jitter
        self.delay = None

    def choose(self, fight, me, opp):
        m = opp.move
        if m and opp.phase == "startup":
            left = m["startup"] - opp.frame
            if self.delay is None:
                self.delay = self.rng.randint(*self.jitter)
            if left <= me.parry_frames - 2 - self.delay:
                self.delay = None
                return "block"
            return None
        self.delay = None
        if opp.state in ("stagger", "hurt") or (opp.phase == "recovery"):
            return self.rng.choice(("light", "heavy"))
        if self.wait > 0:
            self.wait -= 1
            return None
        self.wait = self.rng.randint(25, 60)
        return "light"


BOTS = {c.name: c for c in (Aggressor, Pattern, RandomBot, Reactive)}
