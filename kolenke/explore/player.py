"""Басты кейіпкердің қозғалысы (A/D немесе ←→) жылдамдану мен тежелумен."""
import math

SPEED = 300          # px/сек, ең жоғары жылдамдық
ACCEL = 11.0         # жылдамдану/тежелу қарқыны (1/сек)
MARGIN = 50          # локация шетінен қашықтық


class Player:
    def __init__(self, x):
        self.x = float(x)
        self.vx = 0.0
        self.facing = 1       # 1 — оңға, -1 — солға
        self.walk_phase = 0.0

    @property
    def moving(self):
        return abs(self.vx) > 25

    def update(self, dt, left, right, width):
        """left/right — қазір басулы ма. Локация шегінде қалады."""
        direction = (1 if right else 0) - (1 if left else 0)
        if direction:
            self.facing = direction
        target = direction * SPEED
        self.vx += (target - self.vx) * min(1.0, ACCEL * dt)
        self.x += self.vx * dt
        if self.moving:
            self.walk_phase += dt * 10 * abs(self.vx) / SPEED
        else:
            self.walk_phase = 0.0
        if self.x < MARGIN or self.x > width - MARGIN:
            self.x = max(MARGIN, min(width - MARGIN, self.x))
            self.vx = 0.0

    @property
    def swing(self):
        """Аяқ ұлғаюы -1..1 (анимация үшін)."""
        return math.sin(self.walk_phase) if self.moving else 0.0
