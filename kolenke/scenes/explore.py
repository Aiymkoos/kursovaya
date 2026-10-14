"""Жатақханада жүру: қозғалыс, жарық, боран, есіктер, сөйлесу мен шайқасты бастау."""
import math

import pygame

from kolenke.core.assets import ROOT
from kolenke.core.scene import Scene
from kolenke.explore.locations import load_locations
from kolenke.explore.player import Player
from kolenke.render.corruption import draw_corruption, hidden, protagonist_detail
from kolenke.render.artscene import AMBIENT as ART_AMBIENT, ArtBackdrop, draw_door_marker
from kolenke.render.effects import Fade
from kolenke.render.lighting import Lighting, make_vignette
from kolenke.render.particles import Blizzard, ParticleSystem
from kolenke.render.scenery import GROUND, build_scenery
from kolenke.render.silhouette import draw_silhouette
from kolenke.render.sprite import draw_sprite, has_sprite
from kolenke.render.ui import draw_journal_counter, draw_night_indicator
from kolenke.scenes.dialogue import DialogueScene, JournalScene
from kolenke.scenes.fight import FightScene

LOCATIONS_PATH = ROOT / "kolenke" / "data" / "locations.json"
DATA_DIR = ROOT / "kolenke" / "data"
PLAYER_ACCENT = (110, 170, 230)
WHITE = (230, 230, 230)
GREY = (120, 120, 120)
ACCENT = (200, 60, 60)
CAM_LERP = 6.0
NIGHT_NPCS = {}   # кэш: түн -> NPC тізімі


class ExploreScene(Scene):
    def __init__(self, game, start="corridor", night=None):
        super().__init__(game)
        self.night = night or game.night
        self.locs = load_locations(LOCATIONS_PATH)
        self._scenery = {}
        self._art = {}
        self.t = 0.0
        w, h = game.screen.get_size()
        self.size = (w, h)
        self.blizzard = Blizzard(w, h, count=380, wind=-180)
        self.dust = ParticleSystem()
        self.lighting = Lighting((w, h))
        self.vignette = make_vignette((w, h))
        self.fade = Fade((w, h))
        self._summary_shown = False
        self._reset(start)

    def _reset(self, start="corridor"):
        self.loc = self.locs[start]
        self.player = Player(self.loc.start)
        self.cam = self._target_cam()
        self._last_swing = 0.0
        self._summary_shown = False

    # --- көмекші ---
    def _backdrop(self):
        """Дайын сурет фоны (assets/bg) немесе None — сонда кодпен сызылған декорация."""
        key = self.loc.id
        if key not in self._art:
            self._art[key] = ArtBackdrop.load(self.loc, self.size)
        return self._art[key]

    @property
    def scenery(self):
        key = (self.loc.id, self.night)
        if key not in self._scenery:
            self._scenery[key] = build_scenery(self.loc, self.night)
        return self._scenery[key]

    def _target_cam(self):
        return max(0.0, min(self.loc.width - self.game.screen.get_width(),
                            self.player.x - self.game.screen.get_width() / 2))

    # --- NPC күйі ---
    def _fight_won(self, name):
        return bool(self.game.flags.get(name + "_fight_won"))

    def _talk_done(self, o):
        return bool(self.game.flags.get(o.done_flag))

    def _next_enemy(self, o):
        """Диалогтан кейін: осы NPC үшін әлі жеңілмеген бірінші қарсылас."""
        for name in o.enemies(self.game.flags):
            if not self._fight_won(name):
                return name
        return None

    def _npc_finished(self, o):
        if not self._talk_done(o):
            return False
        return self._next_enemy(o) is None

    def _npc_objects(self, night=None):
        night = night or self.night
        return [o for loc in self.locs.values() for o in loc.objects
                if o.kind == "npc" and o.active(night)]

    def night_complete(self):
        npcs = self._npc_objects()
        return bool(npcs) and all(self._npc_finished(o) for o in npcs)

    def _visible_npc(self, o):
        return o.active(self.night) and not self.game.flags.get(o.who + "_killed")

    def interactables(self):
        out = []
        for o in self.loc.objects:
            if not o.active(self.night):
                continue
            if o.kind == "npc" and self._npc_finished(o):
                continue
            if abs(self.player.x - o.x) <= o.w / 2 + 40:
                out.append(o)
        return sorted(out, key=lambda o: abs(self.player.x - o.x))

    @property
    def near(self):
        found = self.interactables()
        return found[0] if found else None

    def _prompt_label(self, o):
        if o.kind == "npc" and self._talk_done(o):
            enemy = self._next_enemy(o)
            if enemy:
                return "obj_fight_" + enemy
        return o.label

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
            self.game.audio.play("click", 0.6)
            if obj.kind == "door":
                self.game.audio.play("door", 0.7)
                self.fade.start(lambda o=obj: self._go(o))
            elif obj.kind == "npc":
                if self._talk_done(obj):
                    enemy = self._next_enemy(obj)
                    if enemy:
                        self.game.push(FightScene(self.game, enemy, night=self.night))
                else:
                    self.game.push(DialogueScene(self.game, DATA_DIR / obj.dialogue,
                                                 night=self.night))

    def on_resume(self):
        if self.night != self.game.night:      # жаңа түн басталды
            self.night = self.game.night
            self._scenery.clear()
            self._art.clear()
            self._reset("corridor")

    # --- логика ---
    def update(self, dt):
        self.t += dt
        self.game.tick_corruption(dt)
        self.fade.update(dt)
        g = self.game
        if not self.fade.active:
            self.player.update(dt, g.is_held("left"), g.is_held("right"), self.loc.width)
        sw = self.player.swing
        if self.player.moving and sw * self._last_swing < 0:  # қадам -> шаң және дыбыс
            self.game.audio.play("step", 0.22)
            for k in range(3):
                self.dust.emit(self.player.x - self.player.facing * 8, GROUND - 4,
                               -self.player.facing * 30 + (hash((self.t, k)) % 40 - 20),
                               -25 - (hash((k, self.t)) % 20), 0.5, 3, (120, 112, 105), 40)
        self._last_swing = sw
        self.cam += (self._target_cam() - self.cam) * min(1.0, CAM_LERP * dt)
        self.blizzard.update(dt)
        self.dust.update(dt)
        if self.night_complete() and not self._summary_shown and not self.fade.active:
            self._summary_shown = True
            from kolenke.scenes.night_end import NightEndScene
            self.game.push(NightEndScene(self.game, self.night))

    # --- сызу ---
    def draw(self, surface):
        art = self._backdrop()
        sc = None if art else self.scenery
        w, h = self.size
        cam = int(self.cam)
        if art:
            art.draw(surface, cam, self.player.x)
            for o in self.loc.objects:
                if o.kind == "door" and o.active(self.night):
                    draw_door_marker(surface, o.x - cam, GROUND, o.w, self.t)
            self.blizzard.draw(surface, brightness=0.32)       # ішке түсетін қар
        else:
            surface.blit(sc.surface, (0, 0), pygame.Rect(cam, 0, w, h))
        for wnd in (sc.windows if sc else []):  # терезе артындағы боран
            r = wnd.move(-cam, 0)
            if r.right < 0 or r.left > w:
                continue
            prev = surface.get_clip()
            surface.set_clip(r)
            self.blizzard.draw(surface, brightness=0.9)
            surface.set_clip(prev)
            pygame.draw.line(surface, (10, 12, 16), (r.centerx, r.top), (r.centerx, r.bottom), 4)
            pygame.draw.line(surface, (10, 12, 16), (r.left, r.centery), (r.right, r.centery), 4)
        npcs = [o for o in self.loc.objects if o.kind == "npc" and self._visible_npc(o)]
        for o in npcs:
            self._actor(surface, o.who, o.x - cam, o.accent, -1, 0.0, "body")
        p = self.player
        c = self.game.corruption
        self._actor(surface, "me", p.x - cam, PLAYER_ACCENT, p.facing, p.swing, "body",
                    detail=protagonist_detail(c))
        self.dust.draw(surface, cam)

        lights = (sc.lights if sc else []) + [dict(x=p.x, y=GROUND - 150, r=320, color=(190, 215, 255),
                                                   i=0.9 * (1 - 0.5 * c), flicker=0, seed=0)]
        self.lighting.ambient = ART_AMBIENT if art else sc.ambient
        self.lighting.render(surface, lights, cam, self.t)

        for o in npcs:  # акцент жарықтан кейін — «жарқырайды»
            self._actor(surface, o.who, o.x - cam, o.accent, -1, 0.0, "accent")
        self._actor(surface, "me", p.x - cam, PLAYER_ACCENT, p.facing, p.swing, "accent",
                    detail=protagonist_detail(c))
        for px in (sc.pillars if sc else []):  # алдыңғы план: параллакс 1.25x
            sx = int(px - self.cam * 1.25)
            if -100 < sx < w:
                pygame.draw.rect(surface, (3, 3, 5), (sx - 30, 0, 60, h))
                pygame.draw.line(surface, (22, 24, 30), (sx - 30, 0), (sx - 30, h), 2)
        surface.blit(self.vignette, (0, 0))
        draw_corruption(surface, c, self.t)
        self._draw_hud(surface, cam)
        self.fade.draw(surface)

    def _actor(self, surface, name, x, accent, facing, swing, part, detail=1.0):
        """Кейіпкер: assets/sprites/<аты>.png бар болса сурет (жарықтандыруға дейін),
        болмаса код сызған силуэт (дене — жарыққа дейін, акцент — кейін)."""
        if has_sprite(name):
            if part == "body":
                room = self.loc.width <= self.size[0]           # бөлмеде жиһазға сай үлкенірек
                draw_sprite(surface, name, x, GROUND, facing, swing, self.t, detail,
                            scale=1.25 if room else 1.0)
            return
        draw_silhouette(surface, x, GROUND, accent, facing=facing, swing=swing,
                        t=self.t, part=part, detail=detail if part == "accent" else 1.0)

    def _draw_hud(self, surface, cam):
        s, a = self.game.strings, self.game.assets
        w, h = self.size
        c = self.game.corruption
        if not hidden(c, 0.7):
            draw_night_indicator(surface, a.font(22), s["night_label"].format(n=self.night),
                                 self.night)
        if not hidden(c, 0.55):
            draw_journal_counter(surface, a.font(22), len(self.game.journal), w - 40)
        if not hidden(c, 0.4):
            name = a.font(22).render(s[self.loc.name], True, GREY)
            surface.blit(name, name.get_rect(midtop=(w // 2, 30)))
        if not hidden(c, 0.35):
            hint = a.font(18).render(s["controls_explore"], True, GREY)
            surface.blit(hint, hint.get_rect(center=(w // 2, h - 30)))
        talked = [o for o in self._npc_objects() if self._talk_done(o)]
        if talked and not self.night_complete() and not hidden(c, 0.5):
            msg = a.font(24).render(s["fight_ready_hint"], True, ACCENT)
            surface.blit(msg, msg.get_rect(center=(w // 2, h - 80)))
        obj = self.near
        if obj and not self.fade.active:
            bob = math.sin(self.t * 4) * 4
            x = obj.x - cam
            y = GROUND - 250 + bob
            label = a.font(22).render(s[self._prompt_label(obj)], True, WHITE)
            box = pygame.Rect(0, 0, label.get_width() + 70, 40)
            box.midbottom = (x, y)
            pygame.draw.rect(surface, (8, 8, 12), box, border_radius=8)
            pygame.draw.rect(surface, ACCENT, box, 2, border_radius=8)
            key = a.font(20, bold=True).render("E", True, ACCENT)
            surface.blit(key, (box.left + 16, box.centery - key.get_height() // 2))
            surface.blit(label, (box.left + 50, box.centery - label.get_height() // 2))
