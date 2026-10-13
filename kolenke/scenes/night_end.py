"""Түн соңы қорытындысы және финал (4 аяқталу: құтқарылғандар санына байланысты)."""
import json
import math

import pygame

from kolenke.core.assets import ROOT
from kolenke.core.save import delete_save, save_game
from kolenke.core.scene import Scene
from kolenke.core.text import wrap_text
from kolenke.render.particles import Blizzard
from kolenke.render.portrait import draw_portrait

WHITE = (230, 230, 230)
GREY = (120, 120, 120)
ACCENT = (200, 60, 60)
PLAYER_ACCENT = (110, 170, 230)
FRIENDS = ("darkhan", "zhanel", "madina", "bekzat")
NIGHT_FRIENDS = {1: ("darkhan",), 2: ("zhanel", "madina"), 3: ("bekzat",)}
ACCENTS = {"darkhan": (230, 150, 50), "zhanel": (90, 210, 180),
           "madina": (205, 120, 215), "bekzat": (240, 215, 120)}
GROUND = 600


def saved_count(flags):
    return sum(1 for f in FRIENDS if flags.get(f + "_saved"))


def ending_key(count):
    """4 финал: 0 → 0, 1–2 → «жарым таң», 3, 4. Мәтін 1 және 2 үшін бөлек, атау ортақ."""
    return str(max(0, min(4, count)))


def _gradient(size, top, bottom):
    w, h = size
    surf = pygame.Surface(size)
    for y in range(h):
        k = y / (h - 1)
        pygame.draw.line(surf, tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)),
                         (0, y), (w, y))
    return surf


def _draw_row(surface, names, flags, t, scale, bottom, cx0, step, label_font, big_font,
              strings, lost_color):
    """Достардың портреттері: қайтқандары — адам, қалғандары — көлеңке; астында атауы."""
    for i, name in enumerate(names):
        saved = bool(flags.get(name + "_saved"))
        cx = cx0 + i * step
        draw_portrait(surface, name, "human" if saved else "shadow", cx, bottom, t, True, scale)
        who = big_font.render(strings["who_" + name], True, ACCENTS[name] if saved else lost_color)
        surface.blit(who, who.get_rect(center=(cx, bottom + 22)))
        st = strings["status_saved" if saved else "status_lost"]
        txt = label_font.render(st, True, ACCENTS[name] if saved else lost_color)
        surface.blit(txt, txt.get_rect(center=(cx, bottom + 50)))


class NightEndScene(Scene):
    """«N-түн аяқталды»: кім қайтып келді, кім көлеңкеде қалды. Space — әрі қарай."""

    def __init__(self, game, night):
        super().__init__(game)
        self.night = night
        self.t = 0.0
        w, h = game.screen.get_size()
        self.bg = _gradient((w, h), (10, 12, 22), (26, 30, 46))
        self.snow = Blizzard(w, h, count=140, wind=-120, seed=11)

    def handle_action(self, action):
        if action not in ("next", "confirm"):
            return
        g = self.game
        if self.night < 3:
            g.start_night(self.night + 1)
            save_game(g)
            g.pop()          # ExploreScene.on_resume жаңа түнді бастайды
        else:
            g.pop()
            g.push(EndingScene(g))

    def update(self, dt):
        self.t += dt
        self.game.tick_corruption(dt)
        self.snow.update(dt)

    def draw(self, surface):
        s, a, g = self.game.strings, self.game.assets, self.game
        w, h = surface.get_size()
        surface.blit(self.bg, (0, 0))
        self.snow.draw(surface, brightness=0.5)
        title = a.font(54, bold=True).render(s["night_done_title"].format(n=self.night), True, WHITE)
        surface.blit(title, title.get_rect(center=(w // 2, 120)))
        names = NIGHT_FRIENDS[self.night]
        step = 360
        x0 = w // 2 - (len(names) - 1) * step // 2
        _draw_row(surface, names, g.flags, self.t, 0.68, GROUND, x0, step,
                  a.font(20), a.font(26, bold=True), s, GREY)
        res = a.font(24).render(s["reserve_label"].format(p=g.reserve), True, GREY)
        surface.blit(res, res.get_rect(center=(w // 2, 190)))
        hint = a.font(22).render(s["night_next_hint"] if self.night < 3 else s["night_final_hint"],
                                 True, GREY)
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 22)))


class EndingScene(Scene):
    """Финал: сәуле мөлшері құтқарылғандар санына байланысты; Space — келесі жол."""

    def __init__(self, game):
        super().__init__(game)
        with open(ROOT / "kolenke" / "data" / "endings.json", encoding="utf-8") as f:
            data = json.load(f)
        self.count = saved_count(game.flags)
        self.ending = data[ending_key(self.count)]
        self.index = 0
        self.t = 0.0
        self.shown = 0.0
        w, h = game.screen.get_size()
        d = self.ending["dawn"]
        top = tuple(int(a + (b - a) * d) for a, b in zip((8, 10, 18), (250, 170, 110)))
        bot = tuple(int(a + (b - a) * d) for a, b in zip((20, 24, 38), (255, 225, 170)))
        self.bg = _gradient((w, h), top, bot)
        self.snow = Blizzard(w, h, count=int(160 * (1 - 0.7 * d)), wind=-100, seed=5)

    def on_enter(self):
        self.game.audio.play("chime" if self.count >= 3 else "swell", 0.8)

    @property
    def line(self):
        return self.ending["lines"][self.index]

    def handle_action(self, action):
        if action not in ("next", "confirm"):
            return
        if self.shown < len(self.line):
            self.shown = len(self.line)
        elif self.index + 1 < len(self.ending["lines"]):
            self.index += 1
            self.shown = 0.0
        else:
            delete_save()
            self.game.new_game_state()
            self.game.pop_to_menu()

    def update(self, dt):
        self.t += dt
        self.shown = min(len(self.line), self.shown + 50 * dt)
        self.snow.update(dt)

    def draw(self, surface):
        s, a, g = self.game.strings, self.game.assets, self.game
        w, h = surface.get_size()
        d = self.ending["dawn"]
        surface.blit(self.bg, (0, 0))
        self.snow.draw(surface, brightness=0.8)
        tcol = WHITE if d < 0.6 else (40, 26, 30)
        title = a.font(60, bold=True).render(self.ending["title"], True, tcol)
        surface.blit(title, title.get_rect(center=(w // 2, 110)))
        lost = (110, 110, 124) if d < 0.6 else (90, 66, 70)
        state = "human" if g.corruption < 0.6 else "fading"
        draw_portrait(surface, "me", state, 120, GROUND, self.t, True, 0.56)
        _draw_row(surface, FRIENDS, g.flags, self.t, 0.56, GROUND, 410, 245,
                  a.font(17), a.font(22, bold=True), s, lost)
        font = a.font(30)
        y = 170
        for ln in wrap_text(font, self.line[: int(self.shown)], w - 360):
            surface.blit(font.render(ln, True, tcol), (180, y))
            y += 42
        hint = a.font(20).render(s["ending_hint"], True, GREY if d < 0.6 else (90, 70, 70))
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 18)))
