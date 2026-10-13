import array

import pygame
import pytest

from kolenke.core import audio_synth
from kolenke.core.audio import MOTIF, Audio
from kolenke.core.game import Game
from kolenke.combat.fight import Event
from kolenke.scenes.fight import FightScene


@pytest.mark.parametrize("name", sorted(audio_synth.SOUNDS))
def test_every_sound_is_valid_16bit_audio(name):
    data = audio_synth.SOUNDS[name]()
    assert len(data) % 2 == 0 and len(data) > 500
    samples = array.array("h")
    samples.frombytes(data)
    peak = max(abs(v) for v in samples)
    assert 2000 < peak <= 32767          # үнсіз емес және клиппинг жоқ


def test_blizzard_loop_has_no_click_at_seam():
    s = array.array("h")
    s.frombytes(audio_synth.blizzard())
    jump = abs(s[0] - s[-1])
    typical = max(abs(s[i + 1] - s[i]) for i in range(1000, 2000))
    assert jump <= max(typical * 3, 2500)


def test_motifs_cover_all_four_characters_and_exist():
    assert set(MOTIF) == {"darkhan", "zhanel", "madina", "bekzat"}
    assert all(v in audio_synth.SOUNDS for v in MOTIF.values())
    assert {"knife", "drum", "stitch", "tick"} == set(MOTIF.values())


def test_audio_disabled_is_silent_and_safe(monkeypatch):
    def boom(*a, **k):
        raise pygame.error("no device")
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)
    monkeypatch.setattr(pygame.mixer, "init", boom)
    a = Audio()
    assert a.ok is False
    a.play("hit")
    a.loop("blizzard")      # қате шығармайды
    with pytest.raises(KeyError):
        a.play("nonexistent")


def test_mute_toggle_and_unknown_names():
    a = Audio()
    a.loop("blizzard", 0.3)
    assert a.toggle_mute() is True and a.muted
    a.play("hit")           # өшірулі
    assert a.toggle_mute() is False
    assert a.motif_for("bekzat", "tock") == "tock" and a.motif_for("bekzat", "tick") == "tick"


class Spy:
    ok = True

    def __init__(self):
        self.calls = []

    def play(self, name, volume=1.0):
        self.calls.append(name)

    def loop(self, name, volume=0.3):
        self.calls.append("loop:" + name)

    def motif_for(self, name, move=None):
        return MOTIF.get(name)


class IdleAI:
    def decide(self, fight, me, opp):
        return 0, None, False


def test_fight_events_trigger_matching_sounds():
    g = Game(fullscreen=False)
    try:
        g.audio = Spy()
        sc = FightScene(g, "darkhan", ai=lambda: IdleAI())
        g.push(sc)
        sc._on_event(Event("parry", "darkhan", "player", 600, 500, 0, "overhead"))
        sc._on_event(Event("hit", "darkhan", "player", 600, 500, 18, "overhead", True))
        sc._on_event(Event("block", "darkhan", "player", 600, 500, 1, "overhead"))
        sc._on_event(Event("ko", "player", "darkhan", 600, 500))
        assert g.audio.calls == ["parry", "heavy_hit", "block", "boom"]
        g.audio.calls.clear()
        sc.fight.enemy.start_move("overhead")
        sc.fight.enemy.frame = 1
        sc.fight.frame_no = 77
        sc._audio_cues()
        assert g.audio.calls == ["whoosh", "knife"]     # дайындықта Дарханның пышақ мотиві
    finally:
        pygame.quit()
