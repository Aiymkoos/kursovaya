"""Диалог сахнасы және естеліктер журналы."""
import pygame

from kolenke.core.scene import Scene
from kolenke.core.text import wrap_text
from kolenke.story.graph import DialogueGraph, DialogueRunner

ACCENT = (200, 60, 60)
WHITE = (230, 230, 230)
GREY = (120, 120, 120)
CHARS_PER_SEC = 60
CHOICE_ACTIONS = {"choice1": 0, "choice2": 1, "choice3": 2, "choice4": 3}


class JournalScene(Scene):
    """Tab басқанда ашылатын естеліктер журналы."""

    def handle_action(self, action):
        if action in ("journal", "menu"):
            self.game.pop()

    def draw(self, surface):
        s, a = self.game.strings, self.game.assets
        w, h = surface.get_size()
        title = a.font(40, bold=True).render(s["journal_title"], True, ACCENT)
        surface.blit(title, (80, 60))
        entries = self.game.journal.entries()
        font = a.font(24)
        if not entries:
            surface.blit(font.render(s["journal_empty"], True, GREY), (80, 160))
        y = 150
        for _, mem in entries:
            who = s.get("who_" + mem["who"], mem["who"])
            surface.blit(a.font(20, bold=True).render(who, True, ACCENT), (80, y))
            y += 30
            for line in wrap_text(font, mem["text"], w - 160):
                surface.blit(font.render(line, True, WHITE), (80, y))
                y += 32
            y += 18
        hint = a.font(20).render(s["journal_hint"], True, GREY)
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 40)))


class DialogueScene(Scene):
    def __init__(self, game, graph_path, night=1):
        super().__init__(game)
        self.night = night
        self.graph = DialogueGraph.load(graph_path)
        game.journal.catalog.update(self.graph.memories)
        self.runner = DialogueRunner(self.graph, game.flags, game.journal)
        self.shown = 0.0       # көрсетілген таңба саны (теру эффектісі)
        self.notice_time = 0.0  # «жаңа жазба» хабарының уақыты
        self._known = len(game.journal)
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
                self.game.pop()
            elif r.advance():
                self._reset_text()
        elif action in CHOICE_ACTIONS and self.text_done and r.has_choices:
            if r.choose(CHOICE_ACTIONS[action]):
                self._reset_text()

    def update(self, dt):
        self.shown = min(len(self.text), self.shown + CHARS_PER_SEC * dt)
        self.notice_time = max(0.0, self.notice_time - dt)

    def draw(self, surface):
        s, a, r = self.game.strings, self.game.assets, self.runner
        w, h = surface.get_size()
        night = a.font(22).render(s["night_label"].format(n=self.night), True, GREY)
        surface.blit(night, (40, 30))
        j = a.font(22).render(f"Tab · {len(self.game.journal)}", True, GREY)
        surface.blit(j, (w - j.get_width() - 40, 30))

        node = r.node
        speaker = self.graph.speakers.get(node.get("speaker", ""), "")
        y = 250
        if speaker:
            surface.blit(a.font(30, bold=True).render(speaker, True, ACCENT), (160, y))
            y += 50
        font = a.font(32)
        visible = self.text[: int(self.shown)]
        for line in wrap_text(font, visible, w - 320):
            surface.blit(font.render(line, True, WHITE), (160, y))
            y += 44

        if self.text_done and r.has_choices:
            y += 30
            for n, (_, choice) in enumerate(r.choices(), start=1):
                label = a.font(28).render(f"{n}. {choice['text']}", True, WHITE)
                surface.blit(label, (200, y))
                y += 44
        if self.text_done and r.finished:
            done = a.font(24).render(s["night_done"], True, GREY)
            surface.blit(done, done.get_rect(center=(w // 2, h - 100)))

        hint = a.font(20).render(s["dialogue_hint"], True, GREY)
        surface.blit(hint, hint.get_rect(center=(w // 2, h - 40)))
        if self.notice_time > 0:
            note = a.font(22).render(s["new_memory"], True, ACCENT)
            surface.blit(note, note.get_rect(center=(w // 2, 90)))
