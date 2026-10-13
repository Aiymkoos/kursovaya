import random

from kolenke.combat.ai.adaptive import AdaptiveAI
from kolenke.combat.ai.bots import BOTS
from kolenke.combat.ai.markov import MarkovPredictor
from kolenke.combat.ai.metrics import compare, online_accuracy
from kolenke.combat.fight import Fight


def test_predictor_learns_deterministic_cycle():
    seq = ["light", "light", "heavy", "block"] * 30
    acc, curve = online_accuracy(seq, MarkovPredictor(order=2))
    assert acc > 0.9 and curve[-1] > 0.9


def test_predictor_empty_and_laplace():
    p = MarkovPredictor()
    assert p.predict() == (None, 0.0)
    p.observe("light")
    act, conf = p.predict()
    assert act == "light" and 1 / 3 < conf < 1


def test_predictor_random_input_stays_near_chance():
    rng = random.Random(5)
    seq = [rng.choice(("light", "heavy", "block")) for _ in range(600)]
    assert 0.2 < online_accuracy(seq, MarkovPredictor(order=2))[0] < 0.45


def test_higher_order_beats_baselines_on_pattern():
    seq = ["light", "light", "heavy", "block"] * 40
    r = compare(seq)
    assert r["markov2"] > r["frequency"] + 0.3 and r["markov2"] > r["random"] + 0.3


def test_observe_logs_only_when_prediction_exists():
    p = MarkovPredictor()
    p.observe("light")
    assert p.log == []
    p.observe("heavy")
    assert len(p.log) == 1


def test_adaptive_ai_observes_player_actions():
    f = Fight(enemy_controller=AdaptiveAI(seed=1))
    ai = f.controllers[f.enemy]
    f.player.x, f.enemy.x = 500, 640

    class Seq:
        def __init__(s):
            s.n = 0

        def decide(s, fight, me, opp):
            s.n += 1
            return 0, {3: "light", 40: "heavy", 90: "light"}.get(s.n), False

    f.controllers[f.player] = Seq()
    for _ in range(150):
        f.tick()
    assert ai.predictor.history[:3] == ["light", "heavy", "light"]


def test_feint_cancels_and_punishes_block_habit():
    ai = AdaptiveAI(seed=2, threshold=0.4, wait=(0, 0))
    for _ in range(6):
        ai.predictor.observe("block")
    f = Fight(enemy_controller=ai)
    f.player.x, f.enemy.x = 500, 640

    class Turtle:
        def decide(s, fight, me, opp):
            return 0, ("block" if me.can_act and me.block_cooldown == 0 else None), True

    f.controllers[f.player] = Turtle()
    for _ in range(400):
        f.tick()
    assert ai.stats["feints"] >= 1


def test_cancel_returns_enemy_to_idle_during_startup():
    f = Fight()
    e = f.enemy
    e.start_move("overhead")
    e.frame = 5
    e.update(0, "cancel", False, 400)
    assert e.state == "idle"
    e.start_move("overhead")
    e.frame = 36  # active — тоқтату мүмкін емес
    e.update(0, "cancel", False, 400)
    assert e.state == "overhead"


def test_all_bots_complete_a_fight_deterministically():
    results = []
    for name, cls in BOTS.items():
        f = Fight(enemy_controller=AdaptiveAI(seed=3), player_controller=cls(seed=3))
        for _ in range(3000):
            f.tick()
            if f.over:
                break
        results.append((name, f.over, f.player.hp, f.enemy.hp))
    again = []
    for name, cls in BOTS.items():
        f = Fight(enemy_controller=AdaptiveAI(seed=3), player_controller=cls(seed=3))
        for _ in range(3000):
            f.tick()
            if f.over:
                break
        again.append((name, f.over, f.player.hp, f.enemy.hp))
    assert results == again


def test_adaptation_punishes_habits_but_not_randomness():
    """Эксперименттің қысқа нұсқасы: әдетті ұстанған ботты ИИ жеңеді, кездейсоқ ботқа әсері аз."""
    from kolenke.combat.ai_scripted import ScriptedAI

    def lost(bot_cls, make, n=8):
        total = 0.0
        for i in range(n):
            f = Fight("bekzat", enemy_controller=make(i), player_controller=bot_cls(seed=i))
            while not f.over and f.frame_no < 5400:
                f.tick()
            total += 1 - f.player.hp / f.player.max_hp
        return total / n

    pat = BOTS["pattern"]
    scripted = lost(pat, lambda i: ScriptedAI(seed=1000 + i))
    adaptive = lost(pat, lambda i: AdaptiveAI(seed=1000 + i, threshold=0.55))
    assert adaptive > scripted + 0.15
    rnd = BOTS["random"]
    diff = abs(lost(rnd, lambda i: AdaptiveAI(seed=1000 + i)) -
               lost(rnd, lambda i: ScriptedAI(seed=1000 + i)))
    assert diff < 0.3
