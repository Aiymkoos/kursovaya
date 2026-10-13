"""Бейімделетін қарсылас: ойыншының әдеттерін үйреніп, қарсы тактика таңдайды.

1. Қорғаныс. Ойыншы соққы бастағанда болжам дұрыс болса (conf >= threshold),
   қарсылас реакцияны 0–3 кадрда береді -> парирлеу терезесіне түседі.
   Болжам қате болса, реакция кешеді (адам тәрізді 16–24 кадр).
2. Фінт. «Блок» болжанса: соққыны бастап, ортасында тоқтатады, ойыншының блок
   кулдауынан кейін соғады.
3. Жазалау. Парирленген ойыншыға (stagger) бірден шабуыл жасайды.
Ойыншы әдеттерін өзгертсе, болжам нашарлайды -> қарсылас осалданады.
"""
import random

from kolenke.combat.ai.markov import MarkovPredictor

NIGHT_THRESHOLD = {1: 0.70, 2: 0.55, 3: 0.45}   # 1-түн — оқыту: баяу үйренеді
OBSERVED = ("light", "heavy", "block")
ANTICIPATED_DELAY = (0, 3)     # болжам дұрыс: дереу қорғанады
UNANTICIPATED_DELAY = (16, 24)  # болжам қате: кеш реакция
DEFEND_HOLD = 14               # қорғаныс блогын ұстау (кадр)
DEFEND_TIMEOUT = 20            # қорғанысқа кеш қалса бас тарту


class AdaptiveAI:
    def __init__(self, seed=1, predictor=None, threshold=0.55, adapt=True,
                 wait=(30, 70)):
        self.rng = random.Random(seed)
        self.predictor = predictor or MarkovPredictor(order=2)
        self.threshold = threshold
        self.adapt = adapt
        self.wait_range = wait
        self.wait = self.rng.randint(*wait)
        self.feint_cancel_at = None
        self.punish_wait = 0
        self.defend_at = None
        self.hold_left = 0
        self.last_logged_tick = -1
        self.stats = {"feints": 0, "defends": 0, "anticipated": 0, "punishes": 0,
                      "plain": 0}

    @classmethod
    def for_night(cls, night, seed=1):
        return cls(seed=seed, threshold=NIGHT_THRESHOLD.get(night, 0.55))

    # --- бақылау ---
    def _observe(self, fight, player):
        if not (player.state in OBSERVED and player.frame == 0
                and self.last_logged_tick != fight.frame_no):
            return
        self.last_logged_tick = fight.frame_no
        action = player.state
        pred, conf = self.predictor.predict()
        if self.adapt and action in ("light", "heavy"):
            hit = pred == action and conf >= self.threshold
            delay = self.rng.randint(*(ANTICIPATED_DELAY if hit else UNANTICIPATED_DELAY))
            self.defend_at = fight.frame_no + delay
            self.stats["defends"] += 1
            self.stats["anticipated"] += hit
        self.predictor.observe(action)

    # --- шешім ---
    def decide(self, fight, me, opp):
        self._observe(fight, opp)
        hold = self.hold_left > 0
        if hold:
            self.hold_left -= 1
        if self.defend_at is not None:                      # қорғаныс жоспарланған
            if fight.frame_no > self.defend_at + DEFEND_TIMEOUT:
                self.defend_at = None
            elif fight.frame_no >= self.defend_at:
                if me.can_act:
                    self.defend_at, self.hold_left = None, DEFEND_HOLD
                    return 0, "block", True
                if me.move and me.phase == "startup":
                    return 0, "cancel", False               # өз шабуылын тоқтатып қорғану
        if not me.can_act:
            if (self.feint_cancel_at is not None and me.move
                    and me.phase == "startup" and me.frame >= self.feint_cancel_at):
                self.feint_cancel_at = None
                return 0, "cancel", False
            return 0, None, hold
        toward = 1 if opp.x > me.x else -1
        dist = abs(opp.x - me.x)
        reach = max(m["reach"][0] + m["reach"][1] for m in me.moves.values())
        if self.adapt and opp.state == "stagger" and dist <= reach:   # жазалау
            self.stats["punishes"] += 1
            return 0, self._fastest(me), False
        if self.punish_wait > 0:                    # фінттен кейін: ойыншы блоктан шыққанша
            self.punish_wait -= 1
            if opp.state == "idle" and opp.block_cooldown > 0 or self.punish_wait == 0:
                self.punish_wait = 0
                self.stats["plain"] += 1
                return 0, self._fastest(me), False
            return 0, None, hold
        if dist > reach - 15:
            return toward, None, hold
        if self.wait > 0:
            self.wait -= 1
            return 0, None, hold
        self.wait = self.rng.randint(*self.wait_range)
        pred, conf = self.predictor.predict()
        if self.adapt and pred == "block" and conf >= self.threshold:
            move = self.rng.choice(list(me.moves))
            self.feint_cancel_at = max(4, int(me.moves[move]["startup"] * 0.55))
            self.punish_wait = 50
            self.stats["feints"] += 1
            return 0, move, False
        self.stats["plain"] += 1
        return 0, self.rng.choice(list(me.moves)), False

    @staticmethod
    def _fastest(me):
        return min(me.moves, key=lambda k: me.moves[k]["startup"])
