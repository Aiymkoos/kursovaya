"""Жекпе-жек ядросы: кадр дәлдігіндегі есептеу, hitstop, парирлеу, буфер, естеліктер.

Fight.tick() — бір логикалық кадр. Сызу мен баяулау (slow-mo) сахнада.
"""
from dataclasses import dataclass

from kolenke.combat.fighter import Fighter, load_combat_data
from kolenke.combat.hitbox import GROUND, hitbox, hurtbox
from kolenke.core.input import InputBuffer

STAGGER_BONUS = 1.5       # парирленген жауға қосымша зиян
PARRY_MEMORY_GAIN = 15    # сәтті парирлеу -> естелік жолағы
MEMORY_COST = 33          # бір естелік слотының бағасы
HEAL_AMOUNT = 25
FOCUS_BASE = 180          # кадр (3 с); әр естелік жазбасы +60
FOCUS_PARRY_BONUS = 6     # парирлеу терезесіне қосымша кадр
RESTORE_HP_FRACTION = 0.35
UNKNOWN_TELL_SPEEDUP = 0.7   # белгісіз дайындық қимылы 30% жылдамырақ


@dataclass
class Event:
    type: str            # hit | block | parry | ko | mem_heal | mem_focus | restore
    attacker: str
    defender: str
    x: float
    y: float
    damage: int = 0
    move: str = ""
    heavy: bool = False


class PlayerController:
    """Ойыншы енгізуі: буфер (6 кадр) + басулы блок. Тек әрекет ете алғанда оқиды."""

    ORDER = ("mem3", "mem2", "mem1", "block", "heavy", "light")

    def __init__(self, buffer, is_held):
        self.buffer = buffer
        self.is_held = is_held

    def decide(self, fight, me, opp):
        walk = (1 if self.is_held("right") else 0) - (1 if self.is_held("left") else 0)
        cmd = None
        if me.can_act:
            for c in self.ORDER:
                if self.buffer.consume(c):
                    cmd = c
                    break
        return walk, cmd, self.is_held("block")


class Fight:
    def __init__(self, enemy_name="darkhan", enemy_controller=None, data=None,
                 player_controller=None, known_tells=None, start_memory=0,
                 enemy_hp_mult=1.0, entries=0):
        """known_tells: жау қимылдарының танылған id-лері (None — барлығы белгілі).
        entries — журналдағы осы кейіпкер туралы жазба саны (естеліктерге әсер етеді)."""
        self.data = data or load_combat_data()
        self.player = Fighter("player", 420, 1, self.data)
        self.enemy = Fighter(enemy_name, 860, -1, self.data)
        self.entries = entries
        self.player.memory = max(0, min(self.player.max_memory, int(start_memory)))
        self.enemy.max_hp = self.enemy.hp = int(self.enemy.max_hp * enemy_hp_mult)
        if known_tells is not None:
            for mid, m in list(self.enemy.moves.items()):
                if m.get("tell_flag") and mid not in known_tells:
                    m = dict(m)
                    m["startup"] = max(10, int(m["startup"] * UNKNOWN_TELL_SPEEDUP))
                    self.enemy.moves[mid] = m
        self.buffer = InputBuffer(window=6)
        self.controllers = {
            self.player: player_controller or PlayerController(self.buffer, lambda a: False),
            self.enemy: enemy_controller,
        }
        self.hitstop = 0
        self.frame_no = 0
        self.focus_left = 0
        self.over = False
        self.winner = None
        self.outcome = None   # "kill" | "restore" | "lose"

    def push_input(self, action):
        self.buffer.push(action)

    # --- естеліктер ---
    @property
    def can_restore(self):
        e = self.enemy
        low = e.hp <= e.max_hp * RESTORE_HP_FRACTION or e.state == "stagger"
        return (self.entries >= 1 and low and e.alive and not self.over
                and self.player.memory >= MEMORY_COST)

    def usable(self, slot):
        p = self.player
        if self.over or p.memory < MEMORY_COST:
            return False
        if slot == 1:
            return p.hp < p.max_hp
        if slot == 2:
            return self.focus_left == 0
        return self.can_restore

    def _use_memory(self, slot):
        p, e = self.player, self.enemy
        if not self.usable(slot):
            return None
        p.memory -= MEMORY_COST
        if slot == 1:
            p.hp = min(p.max_hp, p.hp + HEAL_AMOUNT)
            return Event("mem_heal", p.name, p.name, p.x, GROUND - 100, HEAL_AMOUNT)
        if slot == 2:
            self.focus_left = FOCUS_BASE + 60 * self.entries
            p.parry_frames += FOCUS_PARRY_BONUS
            return Event("mem_focus", p.name, p.name, p.x, GROUND - 100)
        self.over, self.winner, self.outcome = True, p, "restore"
        return Event("restore", p.name, e.name, e.x, GROUND - 100)

    # --- цикл ---
    def tick(self):
        """Бір логикалық кадр. Қайтарады: осы кадрдағы оқиғалар тізімі."""
        if self.over:
            return []
        if self.hitstop > 0:           # hitstop: уақыт қатады, енгізу буфері да
            self.hitstop -= 1
            return []
        self.frame_no += 1
        self.buffer.tick()
        events = []
        if self.focus_left:
            self.focus_left -= 1
            if not self.focus_left:
                self.player.parry_frames -= FOCUS_PARRY_BONUS
        for me, opp in ((self.player, self.enemy), (self.enemy, self.player)):
            ctrl = self.controllers.get(me)
            walk, cmd, hold = ctrl.decide(self, me, opp) if ctrl else (0, None, False)
            if cmd and cmd.startswith("mem"):
                ev = self._use_memory(int(cmd[3]))
                if ev:
                    events.append(ev)
                cmd = None
            if self.over:
                return events
            if me.alive:
                me.update(walk, cmd, hold, opp.x)
        self._separate()
        hits = [ev for ev in (self._resolve(self.player, self.enemy),
                              self._resolve(self.enemy, self.player)) if ev]
        events += hits
        if hits:
            self.hitstop = max(self._stop_for(e) for e in hits)
        for e in (self.player, self.enemy):
            if not e.alive and not self.over:
                self.over = True
                self.winner = self.player if e is self.enemy else self.enemy
                self.outcome = "kill" if e is self.enemy else "lose"
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
