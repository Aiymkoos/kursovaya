"""Басты мәзір және уақытша 1-түн сахнасы."""
import pygame

from kolenke.core.save import has_save, load_game
from kolenke.core.scene import Scene
from kolenke.scenes.explore import ExploreScene

ACCENT = (200, 60, 60)  # бір акцентті түс
WHITE = (230, 230, 230)
GREY = (120, 120, 120)


class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.index = 0
        self._build_items()

    def _build_items(self):
        s = self.game.strings
        self.items = []
        if has_save():
            self.items.append((s["menu_continue"], self._continue))
        self.items += [(s["menu_new_game"], self._new_game), (s["menu_quit"], self.game.quit)]
        self.index = 0

    def on_resume(self):
        self._build_items()

    def _continue(self):
        if load_game(self.game):
            self.game.push(ExploreScene(self.game))

    def _new_game(self):
        self.game.new_game_state()
        self.game.start_night(1)
        self.game.push(ExploreScene(self.game))

    def handle_action(self, action):
        if action == "up":
            self.index = (self.index - 1) % len(self.items)
        elif action == "down":
            self.index = (self.index + 1) % len(self.items)
        elif action == "confirm":
            self.items[self.index][1]()
        elif action == "menu":
            self.game.quit()

    def draw(self, surface):
        s = self.game.strings
        a = self.game.assets
        w, h = surface.get_size()
        title = a.font(96, bold=True).render(s["title"], True, WHITE)
        surface.blit(title, title.get_rect(center=(w // 2, 190)))
        sub = a.font(26).render(s["subtitle"], True, GREY)
        surface.blit(sub, sub.get_rect(center=(w // 2, 260)))
        font = a.font(40)
        for i, (label, _) in enumerate(self.items):
            selected = i == self.index
            text = font.render(label, True, ACCENT if selected else WHITE)
            rect = text.get_rect(center=(w // 2, 400 + i * 70))
            surface.blit(text, rect)
            if selected:
                pygame.draw.line(surface, ACCENT, (rect.left, rect.bottom + 4),
                                 (rect.right, rect.bottom + 4), 2)
        hint = a.font(20).render(s["menu_hint"], True, GREY)
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 40)))
