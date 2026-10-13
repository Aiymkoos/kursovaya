"""Жекпе-жек сахнасы: кадр дәлдігіндегі ядро + кино-эффектілер.

Логика бекітілген 60 Гц қадаммен (Fight.tick), сызу — кез келген FPS-те.
Эффектілер: hitstop, экран дірілі, парирлеудегі баяулау, ұшқындар, жарық жарқылы.
"""
import math
import random

import pygame

from kolenke.combat.ai.adaptive import AdaptiveAI
from kolenke.combat.fight import MEMORY_COST, Fight, PlayerController
from kolenke.combat.setup import RESTORE_RESERVE_COST, fight_params
from kolenke.combat.hitbox import GROUND
from kolenke.core.scene import Scene
from kolenke.explore.locations import Location
from kolenke.render.corruption import draw_corruption, hidden, protagonist_detail
from kolenke.render.effects import ScreenShake
from kolenke.render.fighter_draw import draw_fighter
from kolenke.render.lighting import Lighting, make_vignette
from kolenke.render.particles import Blizzard, ParticleSystem
from kolenke.render.scenery import build_scenery

TICK = 1 / 60
ARENA_ROOM = {"darkhan": "darkhan_room", "zhanel": "girls_room",
              "madina": "girls_room", "bekzat": "bekzat_room"}
WHITE = (230, 230, 230)
GREY = (120, 120, 120)
ACCENT = (200, 60, 60)
SLOW_SCALE = 0.25
SPARK = (255, 220, 150)
PARRY_COL = (170, 220, 255)


class FightScene(Scene):
    def __init__(self, game, enemy="darkhan", night=1, ai=None, seed=None,
                 tells_enabled=True):
        super().__init__(game)
        self.tells_enabled = tells_enabled
        self.enemy_name = enemy
        self.night = night
        self.ai_factory = ai or (lambda: AdaptiveAI.for_night(
            night, seed=random.randint(0, 9999) if seed is None else seed))
        w, h = game.screen.get_size()
        self.size = (w, h)
        self.canvas = pygame.Surface((w, h))
        room = ARENA_ROOM.get(enemy, "darkhan_room")
        self.scenery = build_scenery(Location(room, w, "", w // 2, []))
        self.lighting = Lighting((w, h))
        self.vignette = make_vignette((w, h))
        self.blizzard = Blizzard(w, h, count=260, wind=-180)
        self.particles = ParticleSystem(limit=500)
        self.shake = ScreenShake()
        self.zoom = 0.0          # кино-зум (парирлеу/KO кезінде)
        self.zoom_pt = (w // 2, GROUND - 100)
        self.t = 0.0
        self._start()

    def _start(self):
        params = fight_params(self.game.flags, self.game.journal, self.game.reserve,
                              self.enemy_name)
        self.tells_visible = self.tells_enabled
        self.fight = Fight(self.enemy_name, enemy_controller=self.ai_factory(), **params)
        self.fight.controllers[self.fight.player] = PlayerController(
            self.fight.buffer, self.game.is_held)
        self.acc = 0.0
        self.slow_left = 0.0
        self.time_scale = 1.0
        self.flashes = []     # [x, y, radius, life, max_life, color]
        self.popups = []      # [text, x, y, life, color]
        self.trails = {"player": [], self.enemy_name: []}
        self.result = None
        self.result_delay = 0.0
        self.stats = {"parries": 0, "hits_taken": 0, "hits_given": 0}

    # --- енгізу ---
    def handle_action(self, action):
        if action == "menu":
            self.game.pop()
        elif self.result:
            if action in ("next", "confirm"):
                if self.result == "win":
                    self._finish()
                    self.game.pop()
                else:
                    self._start()
        elif action in ("light", "heavy", "block"):
            self.fight.push_input(action)
        elif action in ("choice1", "choice2", "choice3"):
            self.fight.push_input("mem" + action[-1])

    def _finish(self):
        """Нәтижені флагтарға жазу: өлтіру немесе адамдық кейіпке қайтару."""
        f, name = self.game.flags, self.enemy_name
        f.set(name + "_fight_won")
        if self.fight.outcome == "restore":
            f.set(name + "_saved")
            self.game.reserve = max(0, self.game.reserve - RESTORE_RESERVE_COST)
        else:
            f.set(name + "_killed")

    # --- логика ---
    def update(self, dt):
        self.t += dt
        self.game.tick_corruption(dt)
        self.shake.update(dt)
        self.zoom = max(0.0, self.zoom - dt * 0.22)
        if self.slow_left > 0:
            self.slow_left -= dt
        self.time_scale = SLOW_SCALE if self.slow_left > 0 else min(
            1.0, self.time_scale + dt * 3)
        sim_dt = dt * self.time_scale
        if not self.fight.over or self.result is None:
            self.acc += sim_dt
            n = 0
            while self.acc >= TICK and n < 4:
                self.acc -= TICK
                n += 1
                for ev in self.fight.tick():
                    self._on_event(ev)
        self.particles.update(sim_dt)
        self.blizzard.update(sim_dt)
        self._update_flashes(sim_dt)
        self._update_popups(dt)
        self._update_trails()
        if self.fight.over and self.result is None:
            self.result_delay += dt
            if self.result_delay > (0.9 if self.fight.outcome == "restore" else 1.6):
                self.result = "win" if self.fight.winner is self.fight.player else "lose"

    def _update_flashes(self, dt):
        for f in self.flashes:
            f[3] -= dt
        self.flashes = [f for f in self.flashes if f[3] > 0]

    def _update_popups(self, dt):
        for p in self.popups:
            p[3] -= dt
            p[2] -= 40 * dt
        self.popups = [p for p in self.popups if p[3] > 0]

    def _update_trails(self):
        for name, fighter in ((self.fight.player.name, self.fight.player),
                              (self.enemy_name, self.fight.enemy)):
            tr = self.trails[name]
            if fighter.phase == "active":
                pass  # нүктелер сызу кезінде қосылады
            elif tr:
                tr.pop(0)

    # --- эффектілер ---
    def _on_event(self, ev):
        s = self.game.strings
        if ev.type == "parry":
            self.zoom, self.zoom_pt = 0.07, (ev.x, ev.y)
            self.shake.add(0.55)
            self.slow_left = 0.7
            self._burst(ev.x, ev.y, 34, PARRY_COL, 520)
            self.flashes.append([ev.x, ev.y, 420, 0.35, 0.35, (170, 215, 255)])
            self.popups.append([s["fight_parry"], ev.x, ev.y - 90, 0.9, PARRY_COL])
            if ev.defender == "player":
                self.stats["parries"] += 1
            else:   # Көлеңке ойыншыны «оқыды»
                self.popups.append([s["fight_read"], ev.x, ev.y - 140, 1.2, (230, 90, 90)])
        elif ev.type == "block":
            self.shake.add(0.12)
            self._burst(ev.x, ev.y, 8, (200, 200, 210), 240)
            self.flashes.append([ev.x, ev.y, 180, 0.12, 0.12, (200, 200, 220)])
        elif ev.type == "hit":
            m = self.game.fight_moves[ev.move]
            self.shake.add(m["shake"])
            self._burst(ev.x, ev.y, 10 + int(m["damage"] * 0.8), SPARK, 380)
            self._shadow_motes(ev.x, ev.y, 12 if ev.heavy else 6)
            self.flashes.append([ev.x, ev.y, 260 if ev.heavy else 170, 0.18, 0.18,
                                 (255, 190, 120)])
            if ev.attacker == "player":
                self.stats["hits_given"] += 1
            else:
                self.stats["hits_taken"] += 1
        elif ev.type == "mem_heal":
            self._burst(ev.x, ev.y, 18, (255, 240, 200), 160)
            self.flashes.append([ev.x, ev.y, 300, 0.5, 0.5, (255, 235, 190)])
            self.popups.append([s["fight_heal"], ev.x, ev.y - 70, 0.9, (255, 240, 200)])
        elif ev.type == "mem_focus":
            self.flashes.append([ev.x, ev.y, 300, 0.4, 0.4, (170, 215, 255)])
            self.popups.append([s["fight_focus"], ev.x, ev.y - 70, 0.9, PARRY_COL])
        elif ev.type == "restore":
            self.slow_left = 1.2
            self.flashes.append([ev.x, ev.y, 520, 1.0, 1.0, (255, 245, 220)])
            self._burst(ev.x, ev.y, 60, (255, 245, 220), 260)
            self.popups.append([s["fight_restore"], ev.x, ev.y - 90, 1.6, (255, 245, 220)])
        elif ev.type == "ko":
            self.zoom, self.zoom_pt = 0.11, (ev.x, ev.y)
            self.slow_left = 1.4
            self.shake.add(0.8)
            self._burst(ev.x, ev.y, 50, SPARK, 600)

    def _burst(self, x, y, n, color, speed):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(speed * 0.3, speed)
            self.particles.emit(x, y, math.cos(a) * v, math.sin(a) * v - 80,
                                random.uniform(0.25, 0.6), random.choice((2, 3, 4)),
                                color, 900)

    def _shadow_motes(self, x, y, n):
        for _ in range(n):
            self.particles.emit(x + random.uniform(-14, 14), y + random.uniform(-20, 30),
                                random.uniform(-30, 30), random.uniform(-110, -40),
                                random.uniform(0.6, 1.1), 5, (150, 120, 215), -20)

    # --- сызу ---
    def draw(self, surface):
        c = self.canvas
        w, h = self.size
        sc = self.scenery
        c.blit(sc.surface, (0, 0))
        for wnd in sc.windows:
            prev = c.get_clip()
            c.set_clip(wnd)
            self.blizzard.draw(c, brightness=0.9)
            c.set_clip(prev)
            pygame.draw.line(c, (10, 12, 16), (wnd.centerx, wnd.top), (wnd.centerx, wnd.bottom), 4)
            pygame.draw.line(c, (10, 12, 16), (wnd.left, wnd.centery), (wnd.right, wnd.centery), 4)

        fp, fe = self.fight.player, self.fight.enemy
        spec_p, spec_e = fp.spec, fe.spec
        ap, ae = tuple(spec_p["accent"]), tuple(spec_e["accent"])
        for fighter, accent in ((fe, ae), (fp, ap)):
            reach = draw_fighter(c, fighter, accent, self.t, part="body")
            self._push_trail(fighter, reach)
        self._draw_trails(c)
        self.particles.draw(c)

        lights = list(sc.lights)
        lights.append(dict(x=fp.x, y=GROUND - 150, r=330, color=(190, 215, 255),
                           i=0.85, flicker=0, seed=0))
        for x, y, r, life, mx, color in self.flashes:
            lights.append(dict(x=x, y=y, r=r, color=color, i=min(1.0, life / mx * 1.3),
                               flicker=0, seed=0))
        self.lighting.ambient = sc.ambient
        self.lighting.render(c, lights, 0, self.t)
        cor = self.game.corruption
        draw_fighter(c, fe, ae, self.t, part="accent")
        draw_fighter(c, fp, ap, self.t, part="accent", detail=protagonist_detail(cor))
        self._draw_tell(c, ae)
        c.blit(self.vignette, (0, 0))
        if self.time_scale < 0.6:  # баяулау: суық реңк
            tint = pygame.Surface((w, h))
            tint.fill((10, 22, 40))
            tint.set_alpha(70)
            c.blit(tint, (0, 0))

        surface.fill((0, 0, 0))
        ox, oy = self.shake.offset()
        if self.zoom > 0.004:       # зум: фокус нүктесіне қарай үлкейту
            z = 1 + self.zoom
            big = pygame.transform.smoothscale(c, (int(w * z), int(h * z)))
            fx, fy = self.zoom_pt
            surface.blit(big, (ox - int(fx * self.zoom), oy - int(fy * self.zoom)))
        else:
            surface.blit(c, (ox, oy))
        draw_corruption(surface, cor, self.t)
        self._draw_hud(surface)

    def _draw_tell(self, surface, accent):
        """Дайындық қимылының белгісі: сөйлесуде байқалған детальге ғана көрінеді."""
        e = self.fight.enemy
        m = e.move
        if not (self.tells_visible and m and e.phase == "startup"):
            return
        flag = m.get("tell_flag")
        if flag and not self.game.flags.get(flag):
            return
        su = m["startup"]
        left = su - e.frame
        ready = left <= self.fight.player.parry_frames   # L басатын сәт
        col = (255, 255, 255) if ready else accent
        cx, cy = int(e.x), GROUND - 215
        r = int(46 * (1 - e.frame / su)) + 12
        pygame.draw.circle(surface, col, (cx, cy), r, 3)
        mark = self.game.assets.font(30, bold=True).render("!", True, col)
        surface.blit(mark, mark.get_rect(center=(cx, cy)))

    def _push_trail(self, fighter, reach):
        tr = self.trails[fighter.name]
        if fighter.phase == "active" and reach:
            tr.append(reach[1])
            del tr[:-9]

    def _draw_trails(self, surface):
        for tr in self.trails.values():
            for i in range(1, len(tr)):
                k = i / len(tr)
                v = int(235 * k)
                pygame.draw.line(surface, (v, v, min(255, v + 15)), tr[i - 1], tr[i],
                                 max(1, int(7 * k)))

    def _bar(self, surface, rect, frac, color, align_right=False):
        pygame.draw.rect(surface, (14, 14, 20), rect, border_radius=4)
        fill = rect.copy()
        fill.width = int(rect.width * max(0.0, min(1.0, frac)))
        if align_right:
            fill.right = rect.right
        pygame.draw.rect(surface, color, fill, border_radius=4)
        pygame.draw.rect(surface, (70, 70, 84), rect, 2, border_radius=4)

    def _draw_hud(self, surface):
        s, a = self.game.strings, self.game.assets
        w, h = self.size
        fp, fe = self.fight.player, self.fight.enemy
        ap, ae = tuple(fp.spec["accent"]), tuple(fe.spec["accent"])
        font = a.font(20, bold=True)
        cor = self.game.corruption
        surface.blit(font.render(s["who_player"], True, ap), (40, 22))
        self._bar(surface, pygame.Rect(40, 52, 460, 22), fp.hp / fp.max_hp, ap)
        if not hidden(cor, 0.8):          # 3-түн: қарсылас жолағы жоғала бастайды
            name = font.render(s["who_" + self.enemy_name], True, ae)
            surface.blit(name, (w - 40 - name.get_width(), 22))
            self._bar(surface, pygame.Rect(w - 500, 52, 460, 22), fe.hp / fe.max_hp, ae, True)
        mem = pygame.Rect(40, 82, 300, 12)  # естелік жолағы
        if not hidden(cor, 0.6):
            self._bar(surface, mem, fp.memory / fp.max_memory, (230, 230, 245))
            for i in (1, 2):
                x = mem.x + mem.width * i // 3
                pygame.draw.line(surface, (70, 70, 84), (x, mem.top), (x, mem.bottom), 2)
            surface.blit(a.font(16).render(s["fight_memory"], True, GREY), (348, 79))
        for i in (1, 2, 3):
            if hidden(cor, 0.6):
                break
            ok = self.fight.usable(i)
            pulse = i == 3 and ok and int(self.t * 6) % 2 == 0
            col = (255, 255, 255) if pulse else ((230, 230, 245) if ok else (80, 80, 94))
            surface.blit(a.font(18, bold=ok).render(s[f"slot{i}"], True, col),
                         (40 + (i - 1) * 100, 100))
        pred = getattr(self.fight.controllers.get(self.fight.enemy), "predictor", None)
        if pred and len(pred.log) >= 4 and not hidden(cor, 0.5):     # Көлеңке сені қаншалықты үйренді
            txt = a.font(18).render(
                s["fight_ai_acc"].format(p=int(pred.accuracy * 100)), True, (150, 120, 215))
            surface.blit(txt, (w - 40 - txt.get_width(), 82))
        if self.fight.can_restore and not self.result:
            hint = a.font(24, bold=True).render(s["fight_restore_hint"], True, (255, 245, 220))
            surface.blit(hint, hint.get_rect(center=(w // 2, 130)))
        for text, x, y, life, color in self.popups:
            img = a.font(30, bold=True).render(text, True, color)
            img.set_alpha(int(255 * min(1.0, life / 0.4)))
            surface.blit(img, img.get_rect(center=(x, y)))
        if not hidden(cor, 0.35):
            ctrl = a.font(18).render(s["fight_controls"], True, GREY)
            surface.blit(ctrl, ctrl.get_rect(center=(w // 2, h - 28)))
        if self.result:
            dim = pygame.Surface((w, h))
            dim.set_alpha(150)
            surface.blit(dim, (0, 0))
            title = (s["fight_win_restore"] if self.fight.outcome == "restore"
                     else s["fight_win"]) if self.result == "win" else s["fight_lose"]
            col = WHITE if self.result == "win" else ACCENT
            t1 = a.font(72, bold=True).render(title, True, col)
            surface.blit(t1, t1.get_rect(center=(w // 2, h // 2 - 30)))
            hint = s["fight_continue"] if self.result == "win" else s["fight_retry"]
            t2 = a.font(26).render(hint, True, GREY)
            surface.blit(t2, t2.get_rect(center=(w // 2, h // 2 + 40)))
