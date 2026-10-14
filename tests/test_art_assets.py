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


def test_sprite_missing_falls_back(monkeypatch):
    from kolenke.render import sprite
    monkeypatch.setattr(sprite, "_base", {})
    surf = pygame.Surface((300, 300))
    assert sprite.draw_sprite(surf, "nobody_here", 150, 280) is False
    assert sprite.has_sprite("nobody_here") is False


def test_sprite_is_cropped_scaled_and_drawn(tmp_path, monkeypatch):
    from kolenke.render import sprite
    (tmp_path / "assets" / "sprites").mkdir(parents=True)
    img = pygame.Surface((400, 800), pygame.SRCALPHA)
    pygame.draw.rect(img, (200, 30, 30, 255), (100, 100, 200, 600))      # өрістері мөлдір фигура
    pygame.image.save(img, str(tmp_path / "assets" / "sprites" / "hero.png"))
    monkeypatch.setattr(assets, "ROOT", tmp_path)
    monkeypatch.setattr(assets, "_images", {})
    monkeypatch.setattr(sprite, "_base", {})
    monkeypatch.setattr(sprite, "_tinted", {})
    s = sprite.get_sprite("hero")
    assert s.get_height() == sprite.SPRITE_H and s.get_width() == round(200 * sprite.SPRITE_H / 600)
    surf = pygame.Surface((400, 400))
    assert sprite.draw_sprite(surf, "hero", 200, 300, facing=-1, swing=0.5, t=1.0, detail=0.2)
    assert surf.get_at((200, 250))[:3] != (0, 0, 0)                     # фигура экранда сызылды


def test_artscene_missing_backdrop_falls_back(monkeypatch):
    from kolenke.explore.locations import Location
    from kolenke.render import artscene
    monkeypatch.setattr(artscene, "load_image", lambda *a, **k: None)
    assert artscene.ArtBackdrop.load(Location("corridor", 2400, "", 300, []), (1280, 720)) is None
    assert artscene.ArtBackdrop.load(Location("unknown_loc", 1280, "", 100, []), (1280, 720)) is None


def test_artscene_parallax_and_door_marker():
    from kolenke.explore.locations import Location
    from kolenke.render import artscene
    img = pygame.Surface((1344, 768))
    img.fill((40, 60, 120))
    art = artscene.ArtBackdrop(pygame.transform.smoothscale(img, (1700, 922)), 2400, 1280)
    surf = pygame.Surface((1280, 720))
    art.draw(surf, 0, 300)
    art.draw(surf, 1120, 2000)                         # соңғы камера орны: шектен шықпайды
    assert surf.get_at((640, 360))[:3] == (40, 60, 120)
    artscene.draw_door_marker(surf, 640, 640, 120, 1.0)
