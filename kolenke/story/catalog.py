"""Барлық түндердің естеліктер каталогын жинау (сақтаудан жүктегенде қажет)."""
import json

from kolenke.core.assets import ROOT

DATA_DIR = ROOT / "kolenke" / "data"


def load_catalog(nights=(1, 2, 3)):
    catalog = {}
    for n in nights:
        with open(DATA_DIR / f"night{n}.json", encoding="utf-8") as f:
            catalog.update(json.load(f).get("memories", {}))
    return catalog
