"""Диалог сахнасы (визуалды новелла) және естеліктер журналы."""
import random

import pygame

from kolenke.core.assets import ROOT
from kolenke.core.scene import Scene
from kolenke.core.text import wrap_text
from kolenke.explore.locations import Location
from kolenke.render.corruption import draw_corruption, hidden
from kolenke.render.lighting import Lighting, make_vignette
from kolenke.render.particles import Blizzard
from kolenke.render.portrait import CHARACTERS, draw_portrait
from kolenke.render.scenery import build_scenery
from kolenke.story.graph import DialogueGraph, DialogueRunner

ACCENT = (200, 60, 60)
WHITE = (232, 232, 238)
NARRATOR = (170, 178, 196)
GREY = (125, 125, 140)
CHARS_PER_SEC = 60
CHOICE_ACTIONS = {"choice1": 0, "choice2": 1, "choice3": 2, "choice4": 3}
_bg_cache = {}


def blurred_room(room, size):
    """Бөлме фоны: жарықтандырылып, бұлыңғыр етіледі (новелла фоны)."""
    key = (room, size)
    if key not in _bg_cache:
        w, h = size
        sc = build_scenery(Location(room, w, "", w // 2, []))
        img = sc.surface.copy()
        Lighting(size, sc.ambient).render(img, sc.lights, 0, 0.0)
        small = pygame.transform.smoothscale(img, (w // 10, h // 10))
        small = pygame.transform.smoothscale(small, (w // 25, h // 25))
        img = pygame.transform.smoothscale(small, (w, h))
        lift = pygame.Surface(size)
        lift.fill((20, 22, 34))
        img.blit(lift, (0, 0), special_flags=pygame.BLEND_RGB_ADD)   # қараңғыда да көрінсін
        shade = pygame.Surface(size)
        shade.fill((205, 205, 215))
        img.blit(shade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        _bg_cache[key] = img
    return _bg_cache[key]


def panel(width, height, alpha=215, border=None, radius=14):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (6, 8, 14, alpha), surf.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(surf, border, surf.get_rect(), 2, border_radius=radius)
    return surf


def glitch(text, level, t, node_id):
    """3-түн: мәтіннің кейбір әріптері жоғалады (естеліктер бұзылады)."""
    if level < 0.35:
        return text
    p = (level - 0.35) * 0.3
    bucket = int(t / 1.2)
    out = []
    for i, ch in enumerate(text):
        r = random.Random(hash((i, bucket, node_id)) & 0xFFFFFF)
        out.append("▒" if ch != " " and r.random() < p else ch)
    return "".join(out)


class JournalScene(Scene):
    """Tab басқанда ашылатын естеліктер журналы (кейіпкер бойынша топтастырылған)."""

    def __init__(self, game):
        super().__init__(game)
        self.t = 0.0
        w, h = game.screen.get_size()
        self.size = (w, h)
        self.snow = Blizzard(w, h, count=90, wind=-120, seed=2)

    def handle_action(self, action):
        if action in ("journal", "menu"):
            self.game.pop()

    def update(self, dt):
        self.t += dt
        self.snow.update(dt)

    def draw(self, surface):
        s, a = self.game.strings, self.game.assets
        w, h = self.size
        surface.blit(blurred_room("darkhan_room", self.size), (0, 0))
        dim = pygame.Surface(self.size)
        dim.set_alpha(150)
        surface.blit(dim, (0, 0))
        self.snow.draw(surface, brightness=0.3)
        surface.blit(panel(w - 120, h - 150, 205, (60, 62, 80)), (60, 80))
        title = a.font(38, bold=True).render(s["journal_title"], True, WHITE)
        surface.blit(title, (100, 100))
        entries = self.game.journal.entries()
        font = a.font(23)
        if not entries:
            surface.blit(font.render(s["journal_empty"], True, GREY), (100, 180))
        y = 170
        last_who = None
        for _, mem in sorted(entries, key=lambda e: list(CHARACTERS).index(e[1]["who"])
                             if e[1]["who"] in CHARACTERS else 99):
            who = mem["who"]
            col = CHARACTERS.get(who, ACCENT)
            if who != last_who:
                y += 8 if last_who else 0
                pygame.draw.circle(surface, col, (112, y + 12), 7)
                surface.blit(a.font(22, bold=True).render(s.get("who_" + who, who), True, col),
                             (130, y))
                y += 34
                last_who = who
            for line in wrap_text(font, mem["text"], w - 300):
                if y > h - 110:
                    break
                surface.blit(font.render(line, True, WHITE), (130, y))
                y += 30
            y += 6
        hint = a.font(20).render(s["journal_hint"], True, GREY)
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 48)))


class DialogueScene(Scene):
    def __init__(self, game, graph_path, night=1):
        super().__init__(game)
        self.night = night
        self.graph = DialogueGraph.load(graph_path)
        game.journal.catalog.update(self.graph.memories)
        self.runner = DialogueRunner(self.graph, game.flags, game.journal)
        self.t = 0.0
        self.shown = 0.0       # көрсетілген таңба саны (теру эффектісі)
        self.notice_time = 0.0  # «жаңа жазба» хабарының уақыты
        self._known = len(game.journal)
        w, h = game.screen.get_size()
        self.size = (w, h)
        self.bg = blurred_room(self.graph.bg, self.size)
        self.blizzard = Blizzard(w, h, count=120, wind=-200, seed=3)
        self.vignette = make_vignette((w, h))
        self._reset_text()

    def _reset_text(self):
        self.shown = 0.0
        n = len(self.game.journal)
        if n > self._known:
            self.notice_time = 2.5
        self._known = n

    @property
    def text(self):
        return self.runner.node.get("text", "")

    @property
    def text_done(self):
        return self.shown >= len(self.text)

    def handle_action(self, action):
        r = self.runner
        if action == "journal":
            self.game.push(JournalScene(self.game))
        elif action == "menu":
            self.game.pop()
        elif action == "next":
            if not self.text_done:
                self.shown = len(self.text)
            elif r.finished:
                self.game.flags.set(self.graph.id + "_talk_done")
                self.game.pop()
            elif r.advance():
                self._reset_text()
        elif action in CHOICE_ACTIONS and self.text_done and r.has_choices:
            if r.choose(CHOICE_ACTIONS[action]):
                self._reset_text()

    def update(self, dt):
        self.t += dt
        self.shown = min(len(self.text), self.shown + CHARS_PER_SEC * dt)
        self.notice_time = max(0.0, self.notice_time - dt)
        self.blizzard.update(dt)
        self.game.tick_corruption(dt)

    # --- сызу ---
    def _cast_positions(self):
        cast = self.graph.cast
        if len(cast) == 1:
            return {cast[0]: 880}
        if len(cast) == 2:
            return {cast[0]: 360, cast[1]: 920}
        return {c: 200 + i * 300 for i, c in enumerate(cast)}

    def draw(self, surface):
        s, a, r = self.game.strings, self.game.assets, self.runner
        w, h = self.size
        c = self.game.corruption
        surface.blit(self.bg, (0, 0))
        self.blizzard.draw(surface, brightness=0.3)
        node = r.node
        speaker = node.get("speaker", "")
        for name, cx in self._cast_positions().items():
            active = speaker == name or speaker not in self.graph.cast
            draw_portrait(surface, name, r.states.get(name, "human"), cx, h + 40, self.t, active)
        surface.blit(self.vignette, (0, 0))
        draw_corruption(surface, c, self.t)
        self._draw_box(surface, node, speaker, c)
        if not hidden(c, 0.7):
            night = a.font(22).render(s["night_label"].format(n=self.night), True, GREY)
            surface.blit(night, (40, 30))
        if not hidden(c, 0.55):
            j = a.font(22).render(f"Tab · {len(self.game.journal)}", True, GREY)
            surface.blit(j, (w - j.get_width() - 40, 30))
        if self.notice_time > 0:
            note = a.font(24, bold=True).render(s["new_memory"], True, (255, 230, 170))
            box = panel(note.get_width() + 50, 46, 220, (255, 230, 170))
            surface.blit(box, box.get_rect(center=(w // 2, 90)))
            surface.blit(note, note.get_rect(center=(w // 2, 90)))

    def _draw_box(self, surface, node, speaker, c):
        s, a, r = self.game.strings, self.game.assets, self.runner
        w, h = self.size
        choices = r.choices() if (self.text_done and r.has_choices) else []
        bh = 190 + 54 * len(choices) if choices else 200
        box = pygame.Rect(70, h - bh - 24, w - 140, bh)
        who_col = CHARACTERS.get(speaker, NARRATOR)
        surface.blit(panel(box.width, box.height, 218, (70, 72, 92)), box.topleft)
        pygame.draw.line(surface, who_col, (box.x + 18, box.y + 1), (box.x + 190, box.y + 1), 3)
        name = self.graph.speakers.get(speaker, "")
        if name:
            plate = a.font(28, bold=True).render(name, True, who_col)
            tab = panel(plate.get_width() + 44, 44, 235, who_col, 10)
            surface.blit(tab, (box.x + 24, box.y - 30))
            surface.blit(plate, (box.x + 46, box.y - 24))
        font = a.font(30)
        col = NARRATOR if speaker in ("narrator", "") else WHITE
        text = glitch(self.text[: int(self.shown)], c, self.t, r.node_id)
        y = box.y + 28
        for line in wrap_text(font, text, box.width - 80):
            surface.blit(font.render(line, True, col), (box.x + 40, y))
            y += 42
        if choices:
            y = max(y + 10, box.y + 104)
            for n, (_, ch) in enumerate(choices, start=1):
                row = pygame.Rect(box.x + 40, y, box.width - 80, 44)
                surface.blit(panel(row.width, row.height, 200, (90, 92, 120), 10), row.topleft)
                pygame.draw.circle(surface, ACCENT, (row.x + 26, row.centery), 14)
                num = a.font(20, bold=True).render(str(n), True, WHITE)
                surface.blit(num, num.get_rect(center=(row.x + 26, row.centery)))
                label = a.font(26).render(glitch(ch["text"], c, self.t, r.node_id + str(n)),
                                          True, WHITE)
                surface.blit(label, (row.x + 56, row.centery - label.get_height() // 2))
                y += 54
        elif self.text_done:
            if r.finished:
                done = a.font(22).render(s["night_done"], True, GREY)
                surface.blit(done, (box.right - done.get_width() - 40, box.bottom - 40))
            elif int(self.t * 2) % 2 == 0:       # ▼ — келесі реплика
                pygame.draw.polygon(surface, who_col, [(box.right - 60, box.bottom - 38),
                                                       (box.right - 40, box.bottom - 38),
                                                       (box.right - 50, box.bottom - 24)])
        if not hidden(c, 0.35):
            hint = a.font(18).render(s["dialogue_hint"], True, GREY)
            surface.blit(hint, hint.get_rect(center=(w // 2, h - 12)))
