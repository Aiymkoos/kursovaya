"""Сақтау/жүктеу: JSON. Түн аяқталғанда автосақтау."""
import json
import os
from pathlib import Path

from kolenke.story.catalog import load_catalog
from kolenke.story.flags import Flags
from kolenke.story.journal import Journal

VERSION = 1


def save_path():
    """KOLENKE_SAVE_DIR немесе %APPDATA%/Kolenke (Windows) / ~/.kolenke."""
    base = os.environ.get("KOLENKE_SAVE_DIR")
    if base:
        return Path(base) / "save.json"
    root = os.environ.get("APPDATA")
    return (Path(root) / "Kolenke" if root else Path.home() / ".kolenke") / "save.json"


def has_save(path=None):
    return (path or save_path()).exists()


def save_game(game, path=None):
    path = path or save_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": VERSION,
        "night": game.night,
        "flags": game.flags.to_dict(),
        "journal": game.journal.to_list(),
        "reserve": game.reserve,
        "corruption": game.corruption,
    }
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)   # жартылай жазылған файл қалмауы үшін


def load_game(game, path=None):
    """Сақтауды оқиды. Бүлінген/жоқ файл болса False қайтарады, ойын күйі өзгермейді."""
    path = path or save_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") != VERSION:
            return False
        catalog = load_catalog()
        ids = [i for i in data["journal"] if i in catalog]
        night = int(data["night"])
        if night not in (1, 2, 3):
            return False
        flags = Flags.from_dict(data["flags"])
        reserve = int(data["reserve"])
        corruption = float(data["corruption"])
    except (OSError, ValueError, KeyError, TypeError):
        return False
    game.flags = flags
    game.journal = Journal.from_list(catalog, ids)
    game.reserve = reserve
    game.night = night
    game.corruption = corruption
    return True


def delete_save(path=None):
    try:
        (path or save_path()).unlink()
    except OSError:
        pass
