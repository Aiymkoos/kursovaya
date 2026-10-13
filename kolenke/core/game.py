"""Негізгі ойын циклі: 60 FPS, сахналар стегі, толық экран."""
import pygame

from kolenke.combat.fighter import load_combat_data
from kolenke.core.assets import Assets, load_strings
from kolenke.core.input import InputBuffer, action_for_key
from kolenke.story.flags import Flags
from kolenke.story.catalog import load_catalog
from kolenke.story.journal import Journal

LOGICAL_SIZE = (1280, 720)  # ішкі ажыратымдылық, экранға масштабталады
FPS = 60
FADE_IN = 0.45


class Game:
    def __init__(self, fullscreen=True):
        pygame.init()
        self.fullscreen = fullscreen
        self.screen = self._make_screen()
        pygame.display.set_caption("Көлеңке")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.strings = load_strings()
        self.fight_moves = load_combat_data()["moves"]
        self.input = InputBuffer()
        self.scenes = []
        self.held = set()
        self.fade_in = 0.0     # жаңа сахнаға өткенде жұмсақ ашылу (секунд)
        self._veil = pygame.Surface(LOGICAL_SIZE)
        self.running = True
        self.new_game_state()

    def start_night(self, n):
        self.night = n
        self.corruption = 0.25 if n == 3 else 0.0

    def tick_corruption(self, dt):
        """3-түнде уақыт өткен сайын кейіпкер айнала түседі."""
        if self.night == 3:
            self.corruption = min(0.92, self.corruption + 0.004 * dt)

    def new_game_state(self):
        """Жаңа ойын: флагтар мен журнал тазаланады."""
        self.flags = Flags()
        self.journal = Journal(load_catalog())
        self.reserve = 100   # естелік қоры: адамды қайтарған сайын азаяды
        self.night = 1       # қазіргі түн (1–3)
        self.corruption = 0.0  # 3-түнде басты кейіпкердің өзі айнала бастайды (0..1)

    def _make_screen(self):
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.fullscreen else 0)
        return pygame.display.set_mode(LOGICAL_SIZE, flags)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        pygame.display.toggle_fullscreen()

    # --- сахналар стегі ---
    @property
    def scene(self):
        return self.scenes[-1] if self.scenes else None

    def push(self, scene):
        self.scenes.append(scene)
        scene.on_enter()
        self.fade_in = FADE_IN

    def pop(self):
        if self.scenes:
            self.scenes.pop().on_exit()
        if self.scene:
            self.scene.on_resume()

    def pop_to_menu(self):
        """Мәзірге оралу (стектегі бірінші сахна)."""
        while len(self.scenes) > 1:
            self.scenes.pop().on_exit()
        if self.scene:
            self.scene.on_resume()

    def quit(self):
        self.running = False

    # --- цикл ---
    def is_held(self, action):
        """Перне қазір басулы ма (үздіксіз қозғалыс үшін)."""
        return action in self.held

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYUP:
                action = action_for_key(event.key)
                if action:
                    self.held.discard(action)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue
                action = action_for_key(event.key)
                if action:
                    self.held.add(action)
                    self.input.push(action)
                    if self.scene:
                        self.scene.handle_action(action)

    def step(self, dt):
        """Бір кадр: оқиғалар, логика, сызу. Тестілеуге ыңғайлы бөлек."""
        self.process_events()
        if self.scene:
            self.scene.update(dt)
        self.input.tick()
        self.screen.fill((0, 0, 0))
        if self.scene:
            self.scene.draw(self.screen)
        if self.fade_in > 0:                      # қараңғыдан жұмсақ ашылу
            self.fade_in = max(0.0, self.fade_in - dt)
            self._veil.set_alpha(int(255 * (self.fade_in / FADE_IN) ** 1.5))
            self.screen.blit(self._veil, (0, 0))
        pygame.display.flip()

    def run(self):
        while self.running and self.scenes:
            dt = self.clock.tick(FPS) / 1000.0
            self.step(dt)
        pygame.quit()
