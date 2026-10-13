"""Қарапайым скриптті қарсылас (5-кезеңде бейімделетін ИИ-мен ауысады)."""
import random


class ScriptedAI:
    """Жақындайды, қашықтықта соғады. Соққы аралығы — кездейсоқ күту."""

    def __init__(self, seed=1, wait=(35, 80)):
        self.rng = random.Random(seed)
        self.wait_range = wait
        self.wait = self.rng.randint(*wait)

    def decide(self, fight, me, opp):
        dist = abs(opp.x - me.x)
        walk = 0
        cmd = None
        if me.can_act:
            reach = max(m["reach"][0] + m["reach"][1] for m in me.moves.values())
            if dist > reach - 15:
                walk = 1 if opp.x > me.x else -1
            elif self.wait > 0:
                self.wait -= 1
            else:
                cmd = self.rng.choice(list(me.moves))
                self.wait = self.rng.randint(*self.wait_range)
        return walk, cmd, False
