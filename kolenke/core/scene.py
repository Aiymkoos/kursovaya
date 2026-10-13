"""Сахналардың базалық класы."""


class Scene:
    """Барлық сахналар (мәзір, диалог, жекпе-жек, финал) осыдан туады."""

    def __init__(self, game):
        self.game = game

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle_action(self, action):
        """Әрекет келгенде шақырылады (KEYMAP бойынша)."""

    def update(self, dt):
        """Логиканы жаңарту; dt — секунд."""

    def draw(self, surface):
        """Кадрды сызу."""
