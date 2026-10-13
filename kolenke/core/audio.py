"""Дыбыс менеджері: синтезделген дыбыстар кэші, қайталанатын боран, M — өшіру.

Аудио құрылғы болмаса (немесе mixer қатесі) — ойын үнсіз жұмыс істей береді.
"""
import pygame

from kolenke.core.audio_synth import RATE, SOUNDS

# Кейіпкер мотиві: шайқас/диалогта қайталанатын дыбыс (ТЗ: пышақ, барабан, тігін, метроном)
MOTIF = {"darkhan": "knife", "zhanel": "drum", "madina": "stitch", "bekzat": "tick"}
MOVE_SOUND = {"tock": "tock", "sweep": "tock"}   # метроном: ауыр қимыл — «так»


class Audio:
    def __init__(self, enabled=True):
        self.ok = False
        self.muted = False
        self._cache = {}
        self._loops = {}
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(16)
            self.ok = True
        except pygame.error:
            self.ok = False

    def _sound(self, name):
        if name not in SOUNDS:
            raise KeyError(f"Белгісіз дыбыс: {name}")
        if name not in self._cache:
            self._cache[name] = pygame.mixer.Sound(buffer=SOUNDS[name]())
        return self._cache[name]

    def play(self, name, volume=1.0):
        if name not in SOUNDS:
            raise KeyError(f"Белгісіз дыбыс: {name}")
        if not self.ok or self.muted:
            return
        snd = self._sound(name)
        snd.set_volume(max(0.0, min(1.0, volume)))
        snd.play()

    def loop(self, name, volume=0.3):
        """Фондық қайталау (боран). Қайта шақырса дыбыс деңгейі ғана жаңарады."""
        if name not in SOUNDS:
            raise KeyError(f"Белгісіз дыбыс: {name}")
        if not self.ok:
            return
        snd = self._sound(name)
        snd.set_volume(0.0 if self.muted else volume)
        if name not in self._loops:
            self._loops[name] = (snd, volume)
            snd.play(loops=-1)
        else:
            self._loops[name] = (snd, volume)

    def toggle_mute(self):
        self.muted = not self.muted
        for snd, vol in self._loops.values():
            snd.set_volume(0.0 if self.muted else vol)
        return self.muted

    def motif_for(self, name, move=None):
        """Кейіпкер мотиві (метрономда қимылға қарай тік/так)."""
        if name == "bekzat" and move in MOVE_SOUND:
            return MOVE_SOUND[move]
        return MOTIF.get(name)
