"""Жекпе-жек ядросы: кадр дәлдігіндегі есептеу, hitstop, парирлеу, буфер.

Fight.tick() — бір логикалық кадр. Сызу мен баяулау (slow-mo) сахнада.
"""
from dataclasses import dataclass

from kolenke.combat.fighter import Fighter, load_combat_data
from kolenke.combat.hitbox import GROUND, hitbox, hurtbox
from kolenke.core.input import InputBuffer

STAGGER_BONUS = 1.5     # парирленген жауға қосымша зиян
PARRY_MEMORY_GAIN = 15


@dataclass
class Event:
    type: str            # "hit" | "block" | "parry" | "ko"
    attacker: str
    defender: str
    x: float
    y: float
    damage: int = 0
    move: str = ""
    heavy: bool = False


class PlayerController:
    """Ойыншы енгізуі: буфер (6 кадр) + басулы блок. Тек әрекет ете алғанда оқиды."""

    def __init__(self, buffer, is_held):
        self.buffer = buffer
        self.is_held = is_held

    def decide(self, fight, me, opp):
        walk = (1 if self.is_held("right") else 0) - (1 if self.is_held("left") else 0)
        cmd = None
        if me.can_act:
            for c in ("block", "heavy", "light"):
                if self.buffer.consume(c):
                    cmd = c
                    break
        return walk, cmd, self.is_held("block")


class Fight:
    def __init__(self, enemy_name="darkhan", enemy_controller=None, data=None,
                 player_controller=None):
        self.data = data or load_combat_data()
        self.player = Fighter("player", 420, 1, self.data)
        self.enemy = Fighter(enemy_name, 860, -1, self.data)
        self.buffer = InputBuffer(window=6)
        self.controllers = {
            self.player: player_controller or PlayerController(self.buffer, lambda a: False),
            self.enemy: enemy_controller,
        }
        self.hitstop = 0
        self.frame_no = 0
        self.over = False
        self.winner = None

    def push_input(self, action):
        self.buffer.push(action)

    def _fighters(self):
        return (self.player, self.enemy)

    def tick(self):
        """Бір логикалық кадр. Қайтарады: осы кадрдағы оқиғалар тізімі."""
        if self.over:
            return []
        if self.hitstop > 0:           # hitstop: уақыт қатады, енгізу буфері да
            self.hitstop -= 1
            return []
        self.frame_no += 1
        self.buffer.tick()
        for me, opp in ((self.player, self.enemy), (self.enemy, self.player)):
            ctrl = self.controllers.get(me)
            walk, cmd, hold = ctrl.decide(self, me, opp) if ctrl else (0, None, False)
            if me.alive:
                me.update(walk, cmd, hold, opp.x)
        self._separate()
        events = []
        for atk, dfn in ((self.player, self.enemy), (self.enemy, self.player)):
            ev = self._resolve(atk, dfn)
            if ev:
                events.append(ev)
        if events:
            self.hitstop = max(self._stop_for(e) for e in events)
        for e in (self.player, self.enemy):
            if not e.alive and not self.over:
                self.over = True
                self.winner = self.player if e is self.enemy else self.enemy
                events.append(Event("ko", self.winner.name, e.name, e.x, GROUND - 90))
        return events

    def _stop_for(self, ev):
        if ev.type == "parry":
            return 10
        if ev.type == "block":
            return 3
        return self.data["moves"][ev.move]["hitstop"]

    def _separate(self):
        gap = 56
        d = self.enemy.x - self.player.x
        if abs(d) < gap:
            push = (gap - abs(d)) / 2
            sgn = 1 if d >= 0 else -1
            self.player.x -= sgn * push
            self.enemy.x += sgn * push

    def _resolve(self, atk, dfn):
        m = atk.move
        if not m or atk.phase != "active" or atk.has_hit or not dfn.alive:
            return None
        box = hitbox(atk.x, atk.facing, m)
        hurt = hurtbox(dfn.x)
        if not box.colliderect(hurt):
            return None
        atk.has_hit = True
        inter = box.clip(hurt)
        ix, iy = inter.centerx, inter.centery
        heavy = m["damage"] >= 18
        kdir = atk.facing
        if dfn.blocking and dfn.facing == -atk.facing:
            if dfn.parry_window:
                atk.get_staggered()
                dfn.memory = min(dfn.max_memory, dfn.memory + PARRY_MEMORY_GAIN)
                dfn.stun = 0
                return Event("parry", atk.name, dfn.name, ix, iy, 0, atk.state, heavy)
            dmg = int(m["damage"] * 0.15)
            dfn.take_block(dmg, kdir, m["knock"])
            return Event("block", atk.name, dfn.name, ix, iy, dmg, atk.state, heavy)
        dmg = m["damage"]
        if dfn.state == "stagger":
            dmg = int(dmg * STAGGER_BONUS)
        move_id = atk.state
        dfn.take_hit(dmg, m["hitstun"], kdir, m["knock"])
        return Event("hit", atk.name, dfn.name, ix, iy, dmg, move_id, heavy)
