"""Есепті жинау бағдарламасының тұтастығы: барлық толтырғыш пен сілтеме шешіледі."""
import functools
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location("build_report", ROOT / "tools" / "build_report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@functools.lru_cache(maxsize=1)
def built():
    br = load_builder()
    return br, br.assemble()             # белгісіз {{...}} болса KeyError көтеріледі


def test_all_placeholders_and_refs_resolve():
    _, blocks = built()
    prose = [b for b in blocks if b["t"] != "code"]       # листингте {{ }} код ретінде кездесуі мүмкін
    dump = json.dumps(prose, ensure_ascii=False)
    assert "{{" not in dump and "}}" not in dump


def test_structure_follows_methodical_plan():
    _, blocks = built()
    heads = [b["text"] for b in blocks if b["t"] in ("h1", "h2")]
    expected = ["КІРІСПЕ", "1 ЗЕРТТЕУ БӨЛІМІ", "1.1 Пәндік аумақты сипаттау",
                "1.2 Бағдарламалау құралдарына шолу", "2 ТЕХНОЛОГИЯЛЫҚ БӨЛІМ",
                "2.1 Тапсырманың қойылымы", "2.2 Бағдарламалау тілін таңдау және оның негіздері",
                "3 АРНАЙЫ БӨЛІМ", "3.1 Модульдер, процедуралар және функцияларды сипаттау",
                "3.2 Идентификаторлар кестесі", "ҚОРЫТЫНДЫ", "ҚОЛДАНЫЛҒАН ДЕРЕКТЕР ТІЗІМІ",
                "ҚОСЫМША А. ТЕХНИКАЛЫҚ ТАПСЫРМА", "ҚОСЫМША Ә. ҚОЛДАНУШЫ БАСҚАРУЫ",
                "ҚОСЫМША Б. БАҒДАРЛАМА ЛИСТИНГІ", "ҚОСЫМША В. ҚҰРЫЛЫМДЫҚ СЫЗБА",
                "ҚОСЫМША Г. ФУНКЦИОНАЛДЫҚ СЫЗБА"]
    positions = [heads.index(h) for h in expected]
    assert positions == sorted(positions)          # реті әдістемелік жоспарға сай


def test_listing_covers_every_source_file():
    _, blocks = built()
    listed = {b["title"].split(": ", 1)[1] for b in blocks if b["t"] == "code"}
    for p in (ROOT / "kolenke").rglob("*.py"):
        if p.stat().st_size > 0:
            assert p.relative_to(ROOT).as_posix() in listed, p
