"""Жауынгер: кадрлық ақырлы автомат (FSM).

Күйлер: idle, block, <move id> (соққы), hurt, stagger, dead.
Соққы фазалары: startup -> active (hitbox бар) -> recovery.
Блок: алғашқы PARRY_FRAMES кадр — парирлеу терезесі.
"""
import json

from kolenke.core.assets import ROOT

DATA_PATH = ROOT / "kolenke" / "data" / "moves.json"
ARENA = (150, 1130)


def load_combat_data(path=DATA_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Fighter:
    def __init__(self, name, x, facing, data, spec=None):
        self.name = name
        self.data = data
        self.spec = spec or data["fighters"][name]
        self.moves = {m: data["moves"][m] for m in self.spec["moves"]}
        self.parry_frames = data["parry_frames"]
        self.block_cooldown_len = data["block_cooldown"]
        self.x = float(x)
        self.facing = facing
        self.max_hp = self.hp = self.spec["hp"]
        self.max_memory = 100
        self.memory = 0
        self.speed = self.spec["speed"]
        self.state = "idle"
        self.frame = 0
        self.stun = 0            # hurt/stagger/blockstun ұзақтығы
        self.block_cooldown = 0
        self.has_hit = False
        self.knock = 0.0
        self.flash = 0           # соққы вспышкасы (кадр)
        self.walk_phase = 0.0
        self.walking = False

    # --- сұраныстар ---
    @property
    def move(self):
        return self.moves.get(self.state)

    @property
    def can_act(self):
        return self.state == "idle"

    @property
    def alive(self):
        return self.state != "dead"

    @property
    def phase(self):
        m = self.move
        if not m:
            return None
        if self.frame < m["startup"]:
            return "startup"
        if self.frame < m["startup"] + m["active"]:
            return "active"
        return "recovery"

    @property
    def parry_window(self):
        return self.state == "block" and self.frame < self.parry_frames

    @property
    def blocking(self):
        return self.state == "block"

    # --- логика ---
    def start_move(self, move_id):
        self.state, self.frame, self.has_hit = move_id, 0, False

    def face(self, opp_x):
        self.facing = 1 if opp_x >= self.x else -1

    def update(self, walk, cmd, hold_block, opp_x):
        """Бір логикалық кадр (1/60 с)."""
        if self.flash:
            self.flash -= 1
        if self.block_cooldown:
            self.block_cooldown -= 1
        self.x += self.knock
        self.knock *= 0.78
        self.walking = False
        s = self.state
        if s == "idle":
            self.face(opp_x)
            if walk:
                self.x += walk * self.speed
                self.walking = True
                self.walk_phase += 0.2
            if cmd == "block" and self.block_cooldown == 0:
                self.state, self.frame = "block", 0
            elif cmd in self.moves:
                self.start_move(cmd)
        elif s == "block":
            self.frame += 1
            if self.frame >= self.parry_frames and not hold_block and self.stun == 0:
                self.state = "idle"
                self.block_cooldown = self.block_cooldown_len
            if self.stun:
                self.stun -= 1
        elif s in self.moves:
            if cmd == "cancel" and self.phase == "startup":   # фінт: қимыл тоқтатылады
                self.state, self.frame = "idle", 0
                return
            self.frame += 1
            m = self.moves[s]
            if self.phase in ("startup", "active"):
                self.x += self.facing * m["step"] * (0.5 if self.phase == "startup" else 1.0)
            if self.frame >= m["startup"] + m["active"] + m["recovery"]:
                self.state = "idle"
        elif s in ("hurt", "stagger"):
            self.frame += 1
            if self.frame >= self.stun:
                self.state = "idle"
        self.x = max(ARENA[0], min(ARENA[1], self.x))

    # --- соққы алу ---
    def take_hit(self, damage, hitstun, knock_dir, knock):
        self.hp = max(0, self.hp - damage)
        self.flash = 4
        self.knock = knock_dir * knock
        if self.hp == 0:
            self.state, self.frame = "dead", 0
        else:
            self.state, self.frame, self.stun = "hurt", 0, hitstun

    def take_block(self, damage, knock_dir, knock):
        self.hp = max(1, self.hp - max(1, damage))
        self.knock = knock_dir * knock * 0.5
        self.stun = 8  # blockstun: блоктан тез шыға алмайды

    def get_staggered(self, frames=55):
        self.state, self.frame, self.stun = "stagger", 0, frames
        self.has_hit = True
