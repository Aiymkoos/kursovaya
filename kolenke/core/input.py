"""Пернелерді әрекеттерге сәйкестендіру және енгізу буфері."""
import pygame

# ТЗ бойынша басқару: A/D/←→ қозғалыс, E әрекет, Space реплика, 1–4 таңдау,
# Tab журнал, J/K/L жекпе-жек, ESC мәзір.
KEYMAP = {
    pygame.K_a: "left", pygame.K_LEFT: "left",
    pygame.K_d: "right", pygame.K_RIGHT: "right",
    pygame.K_e: "interact",
    pygame.K_SPACE: "next",
    pygame.K_1: "choice1", pygame.K_2: "choice2",
    pygame.K_3: "choice3", pygame.K_4: "choice4",
    pygame.K_TAB: "journal",
    pygame.K_j: "light", pygame.K_k: "heavy", pygame.K_l: "block",
    pygame.K_ESCAPE: "menu",
    pygame.K_UP: "up", pygame.K_DOWN: "down",
    pygame.K_RETURN: "confirm", pygame.K_KP_ENTER: "confirm",
}


def action_for_key(key):
    """Перне коды бойынша әрекет атауы (жоқ болса None)."""
    return KEYMAP.get(key)


class InputBuffer:
    """Соңғы N кадр ішіндегі басылған әрекеттерді сақтайды.

    Жекпе-жекте соққыны алдын ала басуға мүмкіндік береді (буфер ~6 кадр).
    """

    def __init__(self, window=6):
        self.window = window
        self.frame = 0
        self._events = []  # (кадр, әрекет)

    def push(self, action):
        self._events.append((self.frame, action))

    def tick(self):
        """Кадр санағышын арттырып, ескірген оқиғаларды тастайды."""
        self.frame += 1
        limit = self.frame - self.window
        self._events = [e for e in self._events if e[0] >= limit]

    def consume(self, action):
        """Әрекет буферде болса — алып тастап True қайтарады."""
        for i, (_, a) in enumerate(self._events):
            if a == action:
                del self._events[i]
                return True
        return False
