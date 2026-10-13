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


# ---------- 4-кезең: естеліктер, дайындық белгілері, таңдау әсері ----------
from kolenke.combat.fight import MEMORY_COST
from kolenke.combat.setup import fight_params, known_tells
from kolenke.story.flags import Flags
from kolenke.story.journal import Journal


def mem_duel(plan, memory=100, entries=2, **kw):
    f = Fight(enemy_controller=Script({}), player_controller=Script(plan),
              start_memory=memory, entries=entries, **kw)
    f.player.x, f.enemy.x = 500, 600
    return f


def test_memory_heal_costs_memory_and_heals():
    f = mem_duel({1: "mem1"})
    f.player.hp = 50
    ev = run(f, 3)
    assert types(ev) == ["mem_heal"] and f.player.hp == 75
    assert f.player.memory == 100 - MEMORY_COST


def test_memory_blocked_when_not_enough_memory():
    f = mem_duel({1: "mem1"}, memory=10)
    f.player.hp = 50
    assert run(f, 3) == [] and f.player.hp == 50


def test_focus_extends_parry_window_then_expires():
    f = mem_duel({1: "mem2"}, entries=1)
    run(f, 2)
    assert f.player.parry_frames == 8 + 6 and f.focus_left > 0
    run(f, 300)
    assert f.player.parry_frames == 8 and f.focus_left == 0


def test_restore_needs_low_enemy_hp_and_a_known_memory():
    f = mem_duel({5: "mem3"})
    run(f, 8)
    assert not f.over  # жау әлі күшті
    f2 = mem_duel({5: "mem3"})
    f2.enemy.hp = 10
    ev = run(f2, 8)
    assert "restore" in types(ev) and f2.over and f2.outcome == "restore"
    f3 = mem_duel({5: "mem3"}, entries=0)  # адам туралы ештеңе білмейді
    f3.enemy.hp = 10
    run(f3, 8)
    assert not f3.over


def test_kill_outcome():
    f = duel({}, {})
    f.enemy.hp = 5
    f.controllers[f.player] = Script({1: "light"})
    run(f, 30)
    assert f.outcome == "kill"


def test_unknown_tell_shortens_startup():
    known = Fight(known_tells={"overhead", "slash"})
    blind = Fight(known_tells=set())
    assert blind.enemy.moves["overhead"]["startup"] < known.enemy.moves["overhead"]["startup"]
    assert blind.enemy.moves["overhead"]["startup"] == int(34 * 0.7)
    assert Fight().enemy.moves["overhead"]["startup"] == 34


def test_choices_map_to_fight_params():
    cat = {"m_overhead": {"who": "darkhan", "text": "t"}}
    flags, journal = Flags({"knows_overhead": True, "darkhan_called_name": True}), Journal(cat)
    journal.add("m_overhead")
    data = Fight().data
    assert known_tells(data, "darkhan", flags) == {"overhead"}
    p = fight_params(flags, journal, reserve=80, enemy="darkhan", data=data)
    assert p["start_memory"] == 40 and p["entries"] == 1 and p["enemy_hp_mult"] == 0.85
    p2 = fight_params(Flags(), Journal(cat), 100, "darkhan", data)
    assert p2["known_tells"] == set() and p2["enemy_hp_mult"] == 1.0
