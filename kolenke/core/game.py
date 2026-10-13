"""Негізгі ойын циклі: 60 FPS, сахналар стегі, толық экран."""
import pygame

from kolenke.combat.fighter import load_combat_data
from kolenke.core.assets import Assets, load_strings
from kolenke.core.input import InputBuffer, action_for_key
from kolenke.story.flags import Flags
from kolenke.story.journal import Journal

LOGICAL_SIZE = (1280, 720)  # ішкі ажыратымдылық, экранға масштабталады
FPS = 60


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
        self.running = True
        self.new_game_state()

    def new_game_state(self):
        """Жаңа ойын: флагтар мен журнал тазаланады."""
        self.flags = Flags()
        self.journal = Journal({})

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

    def pop(self):
        if self.scenes:
            self.scenes.pop().on_exit()

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
        pygame.display.flip()

    def run(self):
        while self.running and self.scenes:
            dt = self.clock.tick(FPS) / 1000.0
            self.step(dt)
        pygame.quit()
