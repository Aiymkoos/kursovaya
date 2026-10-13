"""Есептегі 3.1 және 3.2 кестелері нақты кодпен сәйкес болуын тексереді."""
import csv
import importlib
import inspect
import os
import re
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]


def rows(name):
    with open(ROOT / "docs" / "report" / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def resolve(module, qualname):
    obj = importlib.import_module(module)
    for part in qualname.split("."):
        obj = obj.__dict__[part] if inspect.isclass(obj) and part in obj.__dict__ else getattr(obj, part)
    return obj


@pytest.mark.parametrize("row", rows("functions.csv"), ids=lambda r: r["qualname"])
def test_function_rows_match_real_signatures(row):
    obj = resolve(row["module"], row["qualname"])
    assert row["purpose"].strip()
    declared = [p.strip() for p in row["params"].split(",") if p.strip()]
    if isinstance(obj, property):
        pytest.fail(f"{row['qualname']}: property емес, әдіс болуы керек")
    sig = inspect.signature(obj)
    real = [p for p in sig.parameters if p not in ("self", "cls")]
    assert declared == real, f"{row['qualname']}: кестеде {declared}, кодта {real}"


@pytest.mark.parametrize("row", rows("identifiers.csv"), ids=lambda r: r["module"] + ":" + r["name"])
def test_identifier_rows_exist_in_code(row):
    module = importlib.import_module(row["module"])
    src = Path(module.__file__).read_text(encoding="utf-8")
    assert row["meaning"].strip() and row["type"] in ("тұрақты", "класс", "атрибут")
    if "." in row["name"]:
        cls, attr = row["name"].split(".")
        assert hasattr(module, cls)
        assert re.search(rf"self\.{attr}\b", src), f"{row['name']} кодта табылмады"
    else:
        assert hasattr(module, row["name"]), f"{row['name']} модульде жоқ"
        if row["type"] == "класс":
            assert inspect.isclass(getattr(module, row["name"]))
