import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(autouse=True)
def isolated_save_dir(tmp_path, monkeypatch):
    """Тесттер нақты сақтау файлын ешқашан оқымайды/жазбайды."""
    monkeypatch.setenv("KOLENKE_SAVE_DIR", str(tmp_path / "saves"))
