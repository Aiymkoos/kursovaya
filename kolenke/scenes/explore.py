"""Жатақханада жүру: қозғалыс, жарық, боран, есіктер, сөйлесуді бастау."""
import math

import pygame

from kolenke.core.assets import ROOT
from kolenke.core.scene import Scene
from kolenke.explore.locations import load_locations
from kolenke.explore.player import Player
from kolenke.render.effects import Fade
from kolenke.render.lighting import Lighting, make_vignette
from kolenke.render.particles import Blizzard, ParticleSystem
from kolenke.render.scenery import GROUND, build_scenery
from kolenke.render.silhouette import draw_silhouette
from kolenke.render.ui import draw_journal_counter, draw_night_indicator
from kolenke.scenes.dialogue import DialogueScene, JournalScene

LOCATIONS_PATH = ROOT / "kolenke" / "data" / "locations.json"
DATA_DIR = ROOT / "kolenke" / "data"
PLAYER_ACCENT = (110, 170, 230)
WHITE = (230, 230, 230)
GREY = (120, 120, 120)
ACCENT = (200, 60, 60)
CAM_LERP = 6.0


class ExploreScene(Scene):
    def __init__(self, game, start="corridor", night=1):
        super().__init__(game)
        self.night = night
        self.locs = load_locations(LOCATIONS_PATH)
        self.loc = self.locs[start]
        self._scenery = {}
        self.player = Player(self.loc.start)
        w, h = game.screen.get_size()
        self.size = (w, h)
        self.cam = self._target_cam()
        self.t = 0.0
        self.blizzard = Blizzard(w, h, count=380, wind=-180)
        self.dust = ParticleSystem()
        self.lighting = Lighting((w, h))
        self.vignette = make_vignette((w, h))
        self.fade = Fade((w, h))
        self._last_swing = 0.0

    # --- көмекші ---
    @property
    def scenery(self):
        if self.loc.id not in self._scenery:
            self._scenery[self.loc.id] = build_scenery(self.loc)
        return self._scenery[self.loc.id]

    def _target_cam(self):
        return max(0.0, min(self.loc.width - self.game.screen.get_width(),
                            self.player.x - self.game.screen.get_width() / 2))

    def interactables(self):
        out = []
        for o in self.loc.objects:
            if o.kind == "npc" and self.game.flags.get(o.done_flag):
                continue
            if abs(self.player.x - o.x) <= o.w / 2 + 40:
                out.append(o)
        return sorted(out, key=lambda o: abs(self.player.x - o.x))

    @property
    def near(self):
        found = self.interactables()
        return found[0] if found else None

    def _go(self, door):
        self.loc = self.locs[door.to]
        self.player.x = float(door.spawn)
        self.player.vx = 0.0
        self.cam = self._target_cam()

    # --- енгізу ---
    def handle_action(self, action):
        if self.fade.active:
            return
        if action == "menu":
            self.game.pop()
        elif action == "journal":
            self.game.push(JournalScene(self.game))
        elif action == "interact":
            obj = self.near
            if obj is None:
                return
            if obj.kind == "door":
                self.fade.start(lambda o=obj: self._go(o))
            elif obj.kind == "npc":
                self.game.push(DialogueScene(self.game, DATA_DIR / obj.dialogue,
                                             night=obj.night))

    # --- логика ---
    def update(self, dt):
        self.t += dt
        self.fade.update(dt)
        g = self.game
        if not self.fade.active:
            self.player.update(dt, g.is_held("left"), g.is_held("right"), self.loc.width)
        sw = self.player.swing
        if self.player.moving and sw * self._last_swing < 0:  # қадам -> шаң
            for _ in range(3):
                self.dust.emit(self.player.x - self.player.facing * 8, GROUND - 4,
                               -self.player.facing * 30 + (hash((self.t, _)) % 40 - 20),
                               -25 - (hash((_, self.t)) % 20), 0.5, 3, (120, 112, 105), 40)
        self._last_swing = sw
        self.cam += (self._target_cam() - self.cam) * min(1.0, CAM_LERP * dt)
        self.blizzard.update(dt)
        self.dust.update(dt)

    # --- сызу ---
    def draw(self, surface):
        sc = self.scenery
        w, h = self.size
        cam = int(self.cam)
        surface.blit(sc.surface, (0, 0), pygame.Rect(cam, 0, w, h))
        for wnd in sc.windows:  # терезе артындағы боран
            r = wnd.move(-cam, 0)
            if r.right < 0 or r.left > w:
                continue
            prev = surface.get_clip()
            surface.set_clip(r)
            self.blizzard.draw(surface, brightness=0.9)
            surface.set_clip(prev)
            pygame.draw.line(surface, (10, 12, 16), (r.centerx, r.top), (r.centerx, r.bottom), 4)
            pygame.draw.line(surface, (10, 12, 16), (r.left, r.centery), (r.right, r.centery), 4)
        for o in self.loc.objects:
            if o.kind == "npc":
                draw_silhouette(surface, o.x - cam, GROUND, o.accent, facing=-1,
                                t=self.t, part="body")
        p = self.player
        draw_silhouette(surface, p.x - cam, GROUND, PLAYER_ACCENT, p.facing,
                        p.swing, t=self.t, part="body")
        self.dust.draw(surface, cam)

        lights = sc.lights + [dict(x=p.x, y=GROUND - 150, r=320, color=(190, 215, 255),
                                   i=0.9, flicker=0, seed=0)]
        self.lighting.ambient = sc.ambient
        self.lighting.render(surface, lights, cam, self.t)

        for o in self.loc.objects:  # акцент жарықтан кейін — «жарқырайды»
            if o.kind == "npc":
                draw_silhouette(surface, o.x - cam, GROUND, o.accent, facing=-1,
                                t=self.t, part="accent")
        draw_silhouette(surface, p.x - cam, GROUND, PLAYER_ACCENT, p.facing,
                        p.swing, t=self.t, part="accent")
        for px in sc.pillars:  # алдыңғы план: параллакс 1.25x
            sx = int(px - self.cam * 1.25)
            if -100 < sx < w:
                pygame.draw.rect(surface, (3, 3, 5), (sx - 30, 0, 60, h))
                pygame.draw.line(surface, (22, 24, 30), (sx - 30, 0), (sx - 30, h), 2)
        surface.blit(self.vignette, (0, 0))
        self._draw_hud(surface, cam)
        self.fade.draw(surface)

    def _draw_hud(self, surface, cam):
        s, a = self.game.strings, self.game.assets
        w, h = self.size
        draw_night_indicator(surface, a.font(22), s["night_label"].format(n=self.night),
                             self.night)
        draw_journal_counter(surface, a.font(22), len(self.game.journal), w - 40)
        name = a.font(22).render(s[self.loc.name], True, GREY)
        surface.blit(name, name.get_rect(midtop=(w // 2, 30)))
        hint = a.font(18).render(s["controls_explore"], True, GREY)
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 30)))
        if self.game.flags.get("night1_talk_done"):
            msg = a.font(24).render(s["night1_ready"], True, ACCENT)
            surface.blit(msg, msg.get_rect(center=(w // 2, h - 80)))
        obj = self.near
        if obj and not self.fade.active:
            bob = math.sin(self.t * 4) * 4
            x = obj.x - cam
            y = GROUND - 250 + bob
            label = a.font(22).render(s[obj.label], True, WHITE)
            box = pygame.Rect(0, 0, label.get_width() + 70, 40)
            box.midbottom = (x, y)
            pygame.draw.rect(surface, (8, 8, 12), box, border_radius=8)
            pygame.draw.rect(surface, ACCENT, box, 2, border_radius=8)
            key = a.font(20, bold=True).render("E", True, ACCENT)
            surface.blit(key, (box.left + 16, box.centery - key.get_height() // 2))
            surface.blit(label, (box.left + 50, box.centery - label.get_height() // 2))
