"""Курстық жұмыс есебін жинау: docs/report/text/*.md -> JSON -> .docx

Іске қосу:  python tools/build_report.py [шығыс.docx]
Алдын ала: node + npm пакеті docx, LibreOffice (мазмұн беттерін есептеу үшін), pdftotext.
Кестелер CSV-дан, сандар эксперимент нәтижелерінен, листинг бастапқы кодтан автоматты алынады.
"""
import ast
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "report"
TEXT = REPORT / "text"
EXP = ROOT / "docs" / "experiment"
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("KOLENKE_SAVE_DIR", tempfile.mkdtemp())

BODY_FILES = ["00_intro.md", "10_research.md", "20_tech.md", "30_special.md",
              "40_conclusion.md", "50_sources.md"]
APPENDIX_FILES = ["60_appendix_a.md", "61_appendix_e.md"]
CONTENT_DXA = 9355   # A4: 21 см - 3 см (сол) - 1,5 см (оң)

RUN_IN = [
    "Ойын сахнасы мен элементтері.", "Түндердің құрылымы.", "Диалог және флагтар.", "Жекпе-жек.",
    "Бейімделгіш қарсылас.", "Басқару.", "PyGame ортасының ерекшеліктері.",
    "Бағдарламалау ортасының артықшылықтары.", "Тәжірибелік аспектілер.", "Жинау.",
    "Ойынның басталу кезеңі.", "Кейіпкерлер мен нысандарды инициализациялау.", "Негізгі цикл.",
    "Жекпе-жектегі логика.", "Қозғалыс пен соқтығысу.", "Ұпай есебі орнына ойын күйі.",
    "Жеңіс және жеңіліс жағдайындағы хабарламалар.", "Әдістеме.", "Нәтижелер.",
    "Нәтижелерді талдау.", "Бейімделудің жекпе-жекке әсері.", "Қорытынды.",
    "Жобаның тиімділігі мен сенімділігі.", "Практикалық маңызы.", "Мүмкін жетілдіру жолдары:",
    "Жатақханада жүру (Ә.2-сурет).", "Диалог (Ә.4–Ә.6-суреттер).",
    "Жекпе-жек (Ә.9–Ә.11-суреттер).", "Түн қорытындысы және финал (Ә.12–Ә.14-суреттер).",
    "Естеліктер журналы (Ә.7-сурет)", "Бірінші тәсіл — дайын орындалатын файл.",
    "Екінші тәсіл — бастапқы кодтан іске қосу.",
]
PACKAGES = [
    ("core", "core пакеті ойын циклін, сахналар стегін, енгізуді, ресурстарды, сақтауды және дыбысты қамтамасыз етеді."),
    ("story", "story пакеті диалог графын, флагтар жүйесін және естеліктер журналын іске асырады."),
    ("explore", "explore пакеті жатақханада жүру логикасын (басты кейіпкер қозғалысы және локациялар) қамтиды."),
    ("combat", "combat пакеті жекпе-жектің графиксіз ядросын (FSM, hitbox, парирлеу, естеліктер) және бейімделгіш ИИ-ді қамтиды."),
    ("render", "render пакеті жарықтандыруды, портреттерді, бөлшектерді және эффектілерді сызады."),
    ("scenes", "scenes пакеті ойын сахналарын біріктіреді: мәзір, жүру, диалог, жекпе-жек, түн қорытындысы және финал."),
]


# ---------- сандар ----------
def pct(v):
    return f"{float(v) * 100:.1f}".replace(".", ",") + "%"


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def measure_frame_ms():
    import pygame
    from kolenke.core.game import Game
    from kolenke.scenes.explore import ExploreScene
    import time
    g = Game(fullscreen=False)
    g.push(ExploreScene(g))
    g.held.add("right")
    for _ in range(15):
        g.step(1 / 60)
    t0 = time.perf_counter()
    for _ in range(120):
        g.step(1 / 60)
    ms = (time.perf_counter() - t0) / 120 * 1000
    pygame.quit()
    return ms


def project_numbers():
    tests = 0
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    m = re.search(r"(\d+) tests? collected", out)
    if m:
        tests = int(m.group(1))
    lines = 0
    for p in list((ROOT / "kolenke").rglob("*.py")) + [ROOT / "main.py"]:
        lines += len(p.read_text(encoding="utf-8").splitlines())
    return {"tests": str(tests), "loc": f"{round(lines, -2):,}".replace(",", " "),
            "frame_ms": str(max(1, round(measure_frame_ms())))}


def build_vars():
    v = project_numbers()
    for r in read_csv(EXP / "accuracy.csv"):
        for k in ("random", "last", "frequency", "markov1", "markov2", "markov3"):
            v[f"acc:{r['bot']}:{k}"] = pct(r[k])
    for r in read_csv(EXP / "effect.csv"):
        for k in ("player_hp_lost", "enemy_hp_lost", "player_win_rate"):
            v[f"eff:{r['bot']}:{r['ai']}:{k}"] = pct(r[k])
        v[f"eff:{r['bot']}:{r['ai']}:avg_seconds"] = f"{float(r['avg_seconds']):.1f}".replace(".", ",") + " с"
    return v


# ---------- md -> блоктар ----------
class Numbering:
    def __init__(self):
        self.chapter = ""
        self.count = {}
        self.labels = {}

    def set_chapter(self, h1):
        m = re.match(r"^(\d+)\s", h1)
        a = re.match(r"^ҚОСЫМША\s+(\S+?)\.", h1)
        self.chapter = m.group(1) if m else (a.group(1) if a else "")

    def next(self, kind, label=None):
        key = (self.chapter, kind)
        self.count[key] = self.count.get(key, 0) + 1
        num = f"{self.chapter}.{self.count[key]}" if self.chapter else str(self.count[key])
        text = f"{num}-{'кесте' if kind == 'table' else 'сурет'}"
        if label:
            self.labels[label] = text
        return text


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def col_widths(header, rows, total=CONTENT_DXA, size=22):
    """Баған енін мазмұнға қарай бөледі; ең ұзын сөз сыятындай ең төменгі ен сақталады."""
    n = len(header)
    char = int(size * 4.8)                 # Times New Roman: бір таңба ≈ 0,5 кегль (twips)
    cells = [[header[i]] + [str(r[i]) for r in rows] for i in range(n)]
    min_w = [max(len(w) for c in col for w in c.split()) * char + 220 for col in cells]
    weights = [max(8, min(max(len(c) for c in col), 80)) ** 0.85 for col in cells]
    free = total - sum(min_w)
    if free < 0:                           # өте тар болса, барлығын пропорционал кішірейту
        scale = total / sum(min_w)
        widths = [int(m * scale) for m in min_w]
    else:
        ws = sum(weights)
        widths = [int(m + free * w / ws) for m, w in zip(min_w, weights)]
    widths[-1] += total - sum(widths)
    return widths


def table_block(num, caption_text, header, rows, size=22, label=None):
    cap = f"{num.next('table', label)} — {caption_text}"
    return {"t": "table", "caption": cap, "header": header, "rows": rows,
            "widths": col_widths(header, rows, size=size), "size": size}


def parse_md(text, num, auto):
    blocks, lines, i = [], text.splitlines(), 0
    para, pending_cap = [], None

    def flush():
        nonlocal para
        if para:
            t = " ".join(s.strip() for s in para)
            lead = next((p for p in RUN_IN if t.startswith(p)), None)
            blocks.append({"t": "p", "lead": lead or "", "text": t[len(lead):] if lead else t})
            para = []

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush()
        elif s.startswith("### "):
            flush(); blocks.append({"t": "h3", "text": s[4:]})
        elif s.startswith("## "):
            flush(); blocks.append({"t": "h2", "text": s[3:]})
        elif s.startswith("# "):
            flush()
            num.set_chapter(s[2:])
            blocks.append({"t": "h1", "text": s[2:]})
        elif s.startswith("[table:"):
            flush(); pending_cap = s[len("[table:"):-1].strip()
        elif s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            header, body = rows[0], [r for r in rows[2:]]
            blocks.append(table_block(num, pending_cap or "", header, body))
            pending_cap = None
            continue
        elif s.startswith("[image:"):
            flush()
            parts = [x.strip() for x in s[len("[image:"):-1].split("|")]
            path = parts[0]
            width = float(parts[1].split("=")[1])
            label = parts[3].split("=")[1] if len(parts) > 3 else None
            full = (EXP / path.split("/", 1)[1]) if path.startswith("img_exp/") else REPORT / path
            blocks.append({"t": "image", "path": str(full), "width_cm": width,
                           "caption": f"{num.next('figure', label)} — {parts[2]}"})
        elif re.match(r"^\d+\.\s", s):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(lines[i].strip())
                i += 1
            blocks.append({"t": "refs", "items": items})
            continue
        elif s.startswith("- "):
            flush()
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            blocks.append({"t": "bullets", "items": items})
            continue
        elif s.startswith("{{auto:") and s.endswith("}}"):
            flush()
            blocks += auto[s[7:-2]](num)
        else:
            para.append(s)
        i += 1
    flush()
    return blocks


# ---------- автоматты блоктар ----------
def auto_functions(num):
    rows = read_csv(REPORT / "functions.csv")
    out = []
    for pkg, desc in PACKAGES:
        sel = [r for r in rows if r["module"].split(".")[1] == pkg]
        out.append({"t": "p", "lead": "", "text": desc})
        data = []
        for r in sel:
            mod = "/".join(r["module"].split(".")[2:]) + ".py"      # пакет атауы кестеде бар
            data.append([mod, r["qualname"], r["params"] or "—", r["purpose"]])
        out.append(table_block(num, f"{pkg} пакетінің негізгі функциялары мен әдістері",
                               ["Модуль", "Функция / әдіс", "Параметрлері", "Мақсаты"], data, size=20))
    return out


def auto_identifiers(num):
    rows = read_csv(REPORT / "identifiers.csv")
    data = [["/".join(r["module"].split(".")[1:]) + ".py", r["name"], r["type"], r["meaning"]]
            for r in rows]
    return [table_block(num, "Бағдарламаның негізгі идентификаторлары",
                        ["Модуль", "Идентификатор", "Түрі", "Мағынасы"], data, size=20)]


def auto_acc(num):
    rows = read_csv(EXP / "accuracy.csv")
    hdr = ["Бот", "random", "last", "frequency", "markov1", "markov2", "markov3", "ИИ (жекпе-жек)"]
    data = [[r["bot"]] + [pct(r[k]) for k in ("random", "last", "frequency", "markov1",
                                              "markov2", "markov3", "ai_live_accuracy")] for r in rows]
    return [table_block(num, "Болжау дәлдігі: әр бот үшін 30 жекпе-жек, қарсылас — Бекзат", hdr, data,
                        size=22, label="tab_acc")]


def auto_eff(num):
    rows = read_csv(EXP / "effect.csv")
    hdr = ["Бот", "Қарсылас", "Бот жоғалтқан денсаулық", "Қарсылас жоғалтқан денсаулық",
           "Ботның жеңу үлесі", "Орташа ұзақтық, с"]
    names = {"scripted": "бейімделмейтін", "adaptive": "бейімделгіш"}
    data = [[r["bot"], names[r["ai"]], pct(r["player_hp_lost"]), pct(r["enemy_hp_lost"]),
             pct(r["player_win_rate"]), f"{float(r['avg_seconds']):.1f}".replace(".", ",")] for r in rows]
    return [table_block(num, "Бейімделмейтін және бейімделгіш қарсыластың нәтижелері", hdr, data,
                        size=22, label="tab_eff")]


AUTO = {"functions": auto_functions, "identifiers": auto_identifiers,
        "acc_table": auto_acc, "eff_table": auto_eff}


# ---------- листинг ----------
def listing_files():
    order = ["core", "story", "explore", "combat", "render", "scenes"]
    files = [ROOT / "main.py"]
    for pkg in order:
        files += sorted((ROOT / "kolenke" / pkg).rglob("*.py"), key=lambda p: (len(p.parts), str(p)))
    files.append(ROOT / "tools" / "experiment.py")
    return [f for f in files if f.name != "__init__.py" or f.stat().st_size > 0]


def listing_blocks():
    blocks = [
        {"t": "h1", "text": "ҚОСЫМША Б. БАҒДАРЛАМА ЛИСТИНГІ", "pagebreak": True},
        {"t": "p", "lead": "", "text": "Төменде бағдарламаның Python тіліндегі толық бастапқы коды берілген. "
         "Әр файлдың атауы мен қызметі көрсетілген; код түсініктемелермен (docstring және # түсініктемелер) жазылған. "
         "JSON деректері (night1.json, night2.json, night3.json, locations.json, moves.json, strings_kk.json, "
         "endings.json) мәтіндік файлдар ретінде kolenke/data қалтасында жеке сақталады."},
    ]
    for f in listing_files():
        src = f.read_text(encoding="utf-8")
        rel = f.relative_to(ROOT).as_posix()
        doc = (ast.get_docstring(ast.parse(src)) or "").splitlines()
        purpose = doc[0] if doc else ""
        blocks.append({"t": "code", "title": f"Файл: {rel}", "purpose": purpose,
                       "lines": src.expandtabs(4).splitlines()})
    return blocks


def scheme_blocks():
    return [
        {"t": "h1", "text": "ҚОСЫМША В. ҚҰРЫЛЫМДЫҚ СЫЗБА", "pagebreak": True},
        {"t": "image", "path": str(REPORT / "img" / "scheme_structural.png"), "width_cm": 15.0,
         "caption": "В.1-сурет — «Көлеңке» бағдарламасының құрылымдық сызбасы"},
        {"t": "h1", "text": "ҚОСЫМША Г. ФУНКЦИОНАЛДЫҚ СЫЗБА", "pagebreak": True, "landscape": True},
        {"t": "image", "path": str(REPORT / "img" / "scheme_functional.png"), "width_cm": 21.5,
         "caption": "Г.1-сурет — «Көлеңке» бағдарламасының функционалдық сызбасы"},
    ]


# ---------- жинау ----------
def resolve(text, vars_, labels):
    def rep(m):
        key = m.group(1)
        if key.startswith("ref:"):
            return labels[key[4:]]
        if key not in vars_:
            raise KeyError(f"белгісіз толтырғыш: {{{{{key}}}}}")
        return vars_[key]
    return re.sub(r"\{\{([\w:.]+)\}\}", rep, text)


def apply_vars(blocks, vars_, labels):
    for b in blocks:
        for k in ("text", "lead", "caption", "purpose"):
            if k in b and isinstance(b[k], str):
                b[k] = resolve(b[k], vars_, labels)
        if "items" in b:
            b["items"] = [resolve(x, vars_, labels) for x in b["items"]]
        if b.get("t") == "table":
            b["rows"] = [[resolve(c, vars_, labels) for c in r] for r in b["rows"]]


def assemble():
    num = Numbering()
    blocks = []
    for name in BODY_FILES:
        blocks += parse_md((TEXT / name).read_text(encoding="utf-8"), num, AUTO)
    for name in APPENDIX_FILES:
        bs = parse_md((TEXT / name).read_text(encoding="utf-8"), num, AUTO)
        bs[0]["pagebreak"] = True
        blocks += bs
    for b in blocks:
        if b["t"] == "h1" and b["text"] != "КІРІСПЕ" and "pagebreak" not in b:
            b["pagebreak"] = True
    blocks += listing_blocks()
    num.set_chapter("ҚОСЫМША В.")
    blocks += scheme_blocks()
    apply_vars(blocks, build_vars(), num.labels)
    return blocks


def toc_entries(blocks):
    return [(b["t"], b["text"]) for b in blocks if b["t"] in ("h1", "h2")]


def find_pages(pdf, entries, start_page):
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    pages = text.split("\f")
    norm = lambda s: re.sub(r"\s+", "", s)          # регистрсіз емес: «ҚОРЫТЫНДЫ» ≠ «Қорытынды.»
    npages = [norm(p) for p in pages]
    result, cur = [], start_page - 1
    for _, title in entries:
        key = norm(title)[:48]
        for idx in range(cur, len(npages)):
            if key in npages[idx]:
                result.append(idx + 1)
                cur = idx
                break
        else:
            result.append(None)
    return result, len(pages) - (1 if pages and not pages[-1].strip() else 0)


def render(blocks, toc_pages, out):
    payload = {"blocks": blocks, "toc": [{"level": 1 if t == "h1" else 2, "text": x, "page": p}
                                         for (t, x), p in zip(toc_entries(blocks), toc_pages)]}
    tmp = Path(tempfile.mkdtemp()) / "report.json"
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    subprocess.run(["node", str(ROOT / "tools" / "report_docx.js"), str(tmp), str(out)], check=True)


def to_pdf(docx):
    soffice = next(iter(sorted(Path("/root/.claude/skills").rglob("soffice.py"))), None)
    cmd = ([sys.executable, str(soffice)] if soffice else ["soffice"]) + [
        "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)]
    subprocess.run(cmd, check=True, capture_output=True)
    return docx.with_suffix(".pdf")


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT / "Kolenke_kurstyk_zhoba.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    blocks = assemble()
    entries = toc_entries(blocks)
    pages = [0] * len(entries)
    render(blocks, pages, out)                         # 1-өту: мазмұнсыз беттер
    pdf = to_pdf(out)
    pages, total = find_pages(pdf, entries, start_page=4)
    render(blocks, pages, out)                         # 2-өту: беттер нөмірімен
    pdf = to_pdf(out)
    check, total = find_pages(pdf, entries, start_page=4)
    if check != pages:
        render(blocks, check, out)
        pdf = to_pdf(out)
    print("OK:", out, "| бет саны:", total, "| мазмұн:", len(entries), "жол")
    missing = [e[1] for e, p in zip(entries, pages) if p is None]
    if missing:
        print("БЕТІ ТАБЫЛМАДЫ:", missing)


if __name__ == "__main__":
    main()
