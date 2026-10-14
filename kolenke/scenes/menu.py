"""Басты мәзір: кино-композиция (портреттер, боран, жарқыраған тақырып)."""
import math

import pygame

from kolenke.core.assets import load_image
from kolenke.core.save import has_save, load_game
from kolenke.core.scene import Scene
from kolenke.render.lighting import make_vignette
from kolenke.render.particles import Blizzard
from kolenke.render.portrait import draw_portrait
from kolenke.scenes.dialogue import DialogueScene, blurred_room
from kolenke.scenes.explore import DATA_DIR, ExploreScene

ACCENT = (200, 60, 60)
WHITE = (232, 232, 238)
GREY = (125, 125, 140)


def _glow_text(font, text, color, glow_color, spread=14):
    """Жарқылы мәтін: қара түсте бұлыңғыр көшірме (ADD-қа арналған) + анық мәтін."""
    base = font.render(text, True, color)
    w, h = base.get_size()
    pad = spread * 3
    layer = pygame.Surface((w + pad * 2, h + pad * 2))     # альфасыз қара фон
    layer.blit(font.render(text, True, glow_color), (pad, pad))
    small = pygame.transform.smoothscale(layer, (layer.get_width() // 8, layer.get_height() // 8))
    blur = pygame.transform.smoothscale(small, layer.get_size())
    return base, blur, pad


class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.index = 0
        self.t = 0.0
        w, h = game.screen.get_size()
        self.size = (w, h)
        self.art = load_image("bg/menu_art", self.size)         # дайын заставка болса
        self.bg = self.art if self.art is not None else blurred_room("darkhan_room", self.size)
        self.snow = Blizzard(w, h, count=220, wind=-220, seed=21)
        self.vignette = make_vignette((w, h))
        self.title = _glow_text(game.assets.font(110, bold=True), game.strings["title"],
                                WHITE, (210, 90, 90))
        self._build_items()

    def on_enter(self):
        self.game.audio.loop("blizzard", 0.32)
        self.game.audio.loop("music", 0.38)          # фондық музыка (бүкіл ойын бойы)

    def _build_items(self):
        s = self.game.strings
        self.items = []
        if has_save():
            self.items.append((s["menu_continue"], self._continue))
        self.items += [(s["menu_new_game"], self._new_game), (s["menu_quit"], self.game.quit)]
        self.index = next(i for i, it in enumerate(self.items) if it[1] == self._new_game)   # әдепкі: «Жаңа ойын»

    def on_resume(self):
        self._build_items()

    def _continue(self):
        if load_game(self.game):
            self.game.push(ExploreScene(self.game))

    def _new_game(self):
        self.game.new_game_state()
        self.game.start_night(1)
        self.game.push(ExploreScene(self.game))
        self.game.push(DialogueScene(self.game, DATA_DIR / "night0.json", night=0))   # пролог

    def handle_action(self, action):
        if action == "up":
            self.index = (self.index - 1) % len(self.items)
            self.game.audio.play("click", 0.5)
        elif action == "down":
            self.index = (self.index + 1) % len(self.items)
            self.game.audio.play("click", 0.5)
        elif action == "confirm":
            self.game.audio.play("tick", 0.7)
            self.items[self.index][1]()
        elif action == "menu":
            self.game.quit()

    def update(self, dt):
        self.t += dt
        self.snow.update(dt)

    def draw(self, surface):
        s, a = self.game.strings, self.game.assets
        w, h = self.size
        surface.blit(self.bg, (0, 0))
        self.snow.draw(surface, brightness=0.55)
        if self.art is None:
            draw_portrait(surface, "me", "human", 250, h + 60, self.t, True, 0.95)
            draw_portrait(surface, "darkhan", "shadow", w - 250, h + 60, self.t + 1, True, 0.95)
        surface.blit(self.vignette, (0, 0))
        base, blur, pad = self.title
        pulse = 0.75 + 0.25 * math.sin(self.t * 1.7)
        glow = blur.copy()
        glow.fill((int(255 * pulse),) * 3, special_flags=pygame.BLEND_RGB_MULT)
        pos = base.get_rect(center=(w // 2, 190))
        surface.blit(glow, (pos.x - pad, pos.y - pad), special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(base, pos)
        sub = a.font(26).render(s["subtitle"], True, GREY)
        surface.blit(sub, sub.get_rect(center=(w // 2, 275)))
        font = a.font(40)
        y0 = 400
        for i, (label, _) in enumerate(self.items):
            selected = i == self.index
            text = font.render(label, True, WHITE if selected else GREY)
            rect = text.get_rect(center=(w // 2, y0 + i * 70))
            if selected:
                bar = pygame.Surface((rect.width + 120, rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(bar, (200, 60, 60, 60), bar.get_rect(), border_radius=10)
                surface.blit(bar, bar.get_rect(center=rect.center))
                pygame.draw.polygon(surface, ACCENT, [(rect.left - 44, rect.centery - 11),
                                                      (rect.left - 44, rect.centery + 11),
                                                      (rect.left - 24, rect.centery)])
            surface.blit(text, rect)
        hint = a.font(20).render(s["menu_hint"], True, GREY)
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 36)))
