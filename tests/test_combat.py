import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from kolenke.combat.ai_scripted import ScriptedAI
from kolenke.combat.fight import Fight, PlayerController
from kolenke.core.input import InputBuffer


class Script:
    """Тест үшін: кадр нөмірі бойынша дайын командалар."""

    def __init__(self, plan, hold_until=-1):
        self.plan, self.hold_until, self.n = plan, hold_until, 0

    def decide(self, fight, me, opp):
        self.n += 1
        return 0, self.plan.get(self.n), self.n <= self.hold_until


def duel(player_plan, enemy_plan, hold_until=-1):
    f = Fight(enemy_controller=Script(enemy_plan), player_controller=Script(player_plan, hold_until))
    f.player.x, f.enemy.x = 500, 590  # жақын тұр
    return f


def run(f, ticks):
    ev = []
    for _ in range(ticks):
        ev += f.tick()
    return ev


def types(ev):
    return [e.type for e in ev]


def test_unblocked_overhead_hits_player():
    f = duel({}, {1: "overhead"})
    ev = run(f, 60)
    assert types(ev) == ["hit"] and f.player.hp == 100 - 18
    assert ev[0].attacker == "darkhan"


def test_parry_inside_window_staggers_enemy_and_gives_memory():
    # overhead active 34 кадрда; блок 31-кадрда басылса, терезе ашық
    f = duel({31: "block"}, {1: "overhead"}, hold_until=40)
    ev = run(f, 60)
    assert "parry" in types(ev) and f.player.hp == 100
    assert f.player.memory > 0 and f.enemy.state in ("stagger", "idle")


def test_block_too_early_is_plain_block_not_parry():
    f = duel({20: "block"}, {1: "overhead"}, hold_until=45)
    ev = run(f, 60)
    assert types(ev) == ["block"] and 100 - f.player.hp <= 3


def test_riposte_on_staggered_enemy_deals_bonus():
    f = duel({31: "block", 40: "heavy"}, {1: "overhead"}, hold_until=36)
    ev = run(f, 90)
    hits = [e for e in ev if e.type == "hit" and e.attacker == "player"]
    assert hits and hits[0].damage == int(20 * 1.5)


def test_hitstop_freezes_frames():
    f = duel({}, {1: "overhead"})
    for _ in range(100):
        ev = f.tick()
        if ev:
            break
    frame = f.enemy.frame
    assert f.hitstop > 0
    f.tick()
    assert f.enemy.frame == frame  # қатып тұр


def test_parry_spam_prevented_by_cooldown():
    f = Fight(enemy_controller=Script({}), player_controller=Script({1: "block", 12: "block"}))
    run(f, 11)
    assert f.player.state == "idle" and f.player.block_cooldown > 0
    run(f, 3)
    assert f.player.state == "idle"  # кулдаун кезінде қайта блоктай алмайды


def test_buffered_input_executes_after_recovery():
    buf = InputBuffer(window=6)
    f = Fight(enemy_controller=Script({}))
    f.buffer = buf
    f.controllers[f.player] = PlayerController(buf, lambda a: False)
    buf.push("light")
    f.tick()
    assert f.player.state == "light"
    for _ in range(14):  # recovery аяқталуына жақын
        f.tick()
    buf.push("light")     # әлі recovery кезінде басылды
    for _ in range(6):
        f.tick()
    assert f.player.state == "light" and f.player.frame < 6


def test_ko_ends_fight_and_sets_winner():
    f = duel({}, {})
    f.enemy.hp = 5
    f.controllers[f.player] = Script({1: "light"})
    ev = run(f, 30)
    assert "ko" in types(ev) and f.over and f.winner is f.player
    assert f.tick() == []


def test_scripted_ai_attacks_eventually():
    f = Fight(enemy_controller=ScriptedAI(seed=3))
    f.player.x, f.enemy.x = 500, 700
    ev = run(f, 600)
    assert any(e.attacker == "darkhan" for e in ev)
