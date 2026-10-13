"""Экран эффектілері: қараңғыға өту (fade), экран дірілі."""
import random

import pygame


class Fade:
    """Қараңғыға өшу -> callback -> қайта ашылу. Есік ауысуына қолданылады."""

    def __init__(self, size):
        self.overlay = pygame.Surface(size)
        self.overlay.fill((0, 0, 0))
        self.alpha = 0.0
        self.state = "idle"
        self.duration = 0.25
        self.callback = None

    @property
    def active(self):
        return self.state != "idle"

    def start(self, callback, duration=0.25):
        if self.active:
            return
        self.state, self.duration, self.callback = "out", duration, callback

    def update(self, dt):
        if self.state == "out":
            self.alpha = min(255.0, self.alpha + 255 * dt / self.duration)
            if self.alpha >= 255:
                if self.callback:
                    self.callback()
                self.state = "in"
        elif self.state == "in":
            self.alpha = max(0.0, self.alpha - 255 * dt / self.duration)
            if self.alpha <= 0:
                self.state = "idle"

    def draw(self, surface):
        if self.alpha > 0:
            self.overlay.set_alpha(int(self.alpha))
            surface.blit(self.overlay, (0, 0))


class ScreenShake:
    """Trauma-негізді діріл: соққы/парирлеуде add() шақырылады."""

    def __init__(self, max_px=18, decay=2.2):
        self.trauma = 0.0
        self.max_px = max_px
        self.decay = decay

    def add(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - self.decay * dt)

    def offset(self):
        k = self.trauma ** 2 * self.max_px
        return (int(random.uniform(-k, k)), int(random.uniform(-k, k)))
