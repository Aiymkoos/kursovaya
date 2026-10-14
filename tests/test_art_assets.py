"""Дайын суреттер (assets/bg, assets/portraits) болса қолданылады, жоқ болса код сызады."""
import pygame

from kolenke.core import assets
from kolenke.render import portrait


def test_missing_image_returns_none():
    assert assets.load_image("bg/does_not_exist", (100, 50)) is None


def test_image_is_used_when_present(tmp_path, monkeypatch):
    (tmp_path / "assets" / "portraits").mkdir(parents=True)
    img = pygame.Surface((300, 600), pygame.SRCALPHA)
    img.fill((10, 200, 30, 255))
    pygame.image.save(img, str(tmp_path / "assets" / "portraits" / "me_human.png"))
    monkeypatch.setattr(assets, "ROOT", tmp_path)
    monkeypatch.setattr(assets, "_images", {})
    monkeypatch.setattr(portrait, "_cache", {})
    out = portrait.build_portrait("me", "human")
    assert out.get_size() == (portrait.W, portrait.H)
    assert out.get_at((portrait.W // 2, portrait.H - 5))[:3] == (10, 200, 30)


def test_cover_fills_frame(tmp_path, monkeypatch):
    (tmp_path / "assets" / "bg").mkdir(parents=True)
    pygame.image.save(pygame.Surface((400, 100)), str(tmp_path / "assets" / "bg" / "x.png"))
    monkeypatch.setattr(assets, "ROOT", tmp_path)
    monkeypatch.setattr(assets, "_images", {})
    assert assets.load_image("bg/x", (320, 180)).get_size() == (320, 180)
