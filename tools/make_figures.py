"""Есепке арналған екі сызба: құрылымдық (В қосымшасы) және функционалдық (Г қосымшасы).

Фигуралар — әдістемелік нұсқаудағы кестеге сай: терминатор, процесс, енгізу/шығару,
шарт, қалқымалы терезе, құжат, сақталған мәлімет, тікелей мәлімет, ішкі сақтау.
Іске қосу: python tools/make_figures.py [шығыс_папка]
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle, PathPatch
from matplotlib.path import Path as MPath

LW = 1.1
FONT = 6.6


# ---------- фигуралар ----------
def txt(ax, x, y, s, size=FONT, bold=False):
    ax.text(x, y, s, ha="center", va="center", fontsize=size,
            fontweight="bold" if bold else "normal", linespacing=1.15)


def terminator(ax, x, y, s, w=22, h=11):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h/2}",
                                fc="white", ec="black", lw=LW))
    txt(ax, x, y, s)


def process(ax, x, y, s, w=22, h=11):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="black", lw=LW))
    txt(ax, x, y, s)


def inout(ax, x, y, s, w=22, h=11, k=2.6):
    ax.add_patch(Polygon([(x - w / 2 + k, y + h / 2), (x + w / 2 + k, y + h / 2),
                          (x + w / 2 - k, y - h / 2), (x - w / 2 - k, y - h / 2)],
                         closed=True, fc="white", ec="black", lw=LW))
    txt(ax, x, y, s)


def decision(ax, x, y, s, w=24, h=14):
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                         closed=True, fc="white", ec="black", lw=LW))
    txt(ax, x, y, s, size=FONT - 0.4)


def popup(ax, x, y, s, w=22, h=11, k=3.0):
    ax.add_patch(Polygon([(x - w / 2, y), (x - w / 2 + k, y + h / 2), (x + w / 2 - k, y + h / 2),
                          (x + w / 2, y), (x + w / 2 - k, y - h / 2), (x - w / 2 + k, y - h / 2)],
                         closed=True, fc="white", ec="black", lw=LW))
    txt(ax, x, y, s)


def document(ax, x, y, s, w=22, h=11):
    l, r, t, b = x - w / 2, x + w / 2, y + h / 2, y - h / 2
    verts = [(l, t), (r, t), (r, b + 1.6), (r - w * 0.25, b + 3.1), (l + w * 0.25, b), (l, b + 1.6), (l, t)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), fc="white", ec="black", lw=LW))
    txt(ax, x, y + 0.8, s)


def stored(ax, x, y, s, w=22, h=11):
    l, r, t, b = x - w / 2, x + w / 2, y + h / 2, y - h / 2
    verts = [(l + 2.5, t), (r, t), (r - 2.5, y), (r, b), (l + 2.5, b), (l, y), (l + 2.5, t)]
    codes = [MPath.MOVETO, MPath.CURVE3, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CURVE3, MPath.CURVE3]
    # қарапайым қисық: екі жағы иілген
    path = MPath([(l + 2.5, t), (r, t), (r - 2.5, y), (r, b), (l + 2.5, b), (l, y), (l + 2.5, t)],
                 [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CURVE3, MPath.CURVE3])
    ax.add_patch(PathPatch(path, fc="white", ec="black", lw=LW))
    txt(ax, x, y, s)


def cylinder(ax, x, y, s, w=22, h=11):
    ry = 1.8
    ax.add_patch(Rectangle((x - w / 2, y - h / 2 + ry), w, h - 2 * ry, fc="white", ec="none"))
    ax.add_patch(Ellipse((x, y - h / 2 + ry), w, 2 * ry, fc="white", ec="black", lw=LW))
    ax.add_patch(Rectangle((x - w / 2, y - h / 2 + ry), w, h - 2 * ry, fc="white", ec="none"))
    ax.plot([x - w / 2, x - w / 2], [y - h / 2 + ry, y + h / 2 - ry], "k", lw=LW)
    ax.plot([x + w / 2, x + w / 2], [y - h / 2 + ry, y + h / 2 - ry], "k", lw=LW)
    ax.add_patch(Ellipse((x, y + h / 2 - ry), w, 2 * ry, fc="white", ec="black", lw=LW))
    txt(ax, x, y - 0.4, s)


def internal(ax, x, y, s, w=22, h=11):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="black", lw=LW))
    ax.plot([x - w / 2, x + w / 2], [y + h / 2 - 2.2, y + h / 2 - 2.2], "k", lw=LW * 0.8)
    ax.plot([x - w / 2 + 2.2, x - w / 2 + 2.2], [y - h / 2, y + h / 2], "k", lw=LW * 0.8)
    txt(ax, x + 1.0, y - 1.0, s)


def connector(ax, x, y, s, r=2.6):
    ax.add_patch(Ellipse((x, y), 2 * r, 2 * r, fc="white", ec="black", lw=LW))
    txt(ax, x, y, s, size=FONT + 1, bold=True)


def line(ax, pts, arrow=True, both=False, dashed=False, label=None, lpos=None):
    xs, ys = zip(*pts)
    ls = (0, (3, 2)) if dashed else "-"
    ax.plot(xs[:-1] + (xs[-1],) if False else xs, ys, color="black", lw=LW * 0.9, ls=ls,
            solid_capstyle="butt", zorder=1)
    if arrow:
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color="black",
                                                                      lw=LW * 0.9, mutation_scale=7), zorder=3)
    if both:
        ax.annotate("", xy=pts[0], xytext=pts[1], arrowprops=dict(arrowstyle="-|>", color="black",
                                                                    lw=LW * 0.9, mutation_scale=7), zorder=3)
    if label:
        ax.text(*lpos, label, fontsize=FONT, ha="center", va="center", style="italic",
                bbox=dict(fc="white", ec="none", pad=0.5))


# ---------- функционалдық сызба ----------
def functional(path):
    fig = plt.figure(figsize=(11.69, 8.27), dpi=200)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 113)
    ax.axis("off")
    X = [20, 45, 70, 95, 120, 145]
    R1, R2, R3, R4, R5 = 102, 82, 62, 42, 22

    terminator(ax, X[0], R1, "Бастау\n(main.py)")
    popup(ax, X[1], R1, "Басты мәзір:\nЖалғастыру /\nЖаңа ойын / Шығу")
    decision(ax, X[2], R1, "«Жалғастыру»\nжәне сақтау\nбар ма?")
    cylinder(ax, X[3], R1, "Сақтауды\nжүктеу\n(save.json)")
    process(ax, X[4], R1, "Түнді бастау\n(N = 1…3),\nкүйді дайындау")
    connector(ax, 145, R1, "2")
    line(ax, [(31, R1), (34, R1)])
    line(ax, [(56, R1), (58, R1)])
    line(ax, [(82, R1), (84, R1)], label="иә", lpos=(83, R1 + 2.6))
    line(ax, [(106, R1), (109, R1)])
    line(ax, [(70, R1 + 7), (70, 111), (120, 111), (120, R1 + 5.5)],
         label="жоқ: жаңа ойын (күй нөлденеді)", lpos=(95, 111))
    line(ax, [(142.4, R1), (131, R1)])

    connector(ax, 3.2, R2, "1")
    process(ax, X[0], R2, "Жатақханада\nжүру (A/D),\nкамера, жарық")
    inout(ax, X[1], R2, "Енгізу:\nE, Tab, ESC")
    decision(ax, X[2], R2, "E: есік\nнемесе NPC\nжақын ба?")
    decision(ax, X[3], R2, "Диалог\nаяқталған\nба?")
    popup(ax, X[4], R2, "Диалог (граф):\nSpace, 1–4")
    internal(ax, X[5], R2, "Флагтар,\nжурнал\n(ОЗУ)")
    connector(ax, 120, R2 - 10.5, "1")
    line(ax, [(120, R1 - 5.5), (120, 93), (14, 93), (14, R2 + 5.5)])
    line(ax, [(5.8, R2), (9, R2)])
    line(ax, [(31, R2), (34, R2)])
    line(ax, [(56, R2), (58, R2)])
    line(ax, [(82, R2), (83, R2)], label="иә", lpos=(82.6, R2 + 2.6))
    line(ax, [(70, R2 + 7), (70, 90), (28, 90), (28, R2 + 5.5)], label="жоқ", lpos=(50, 90))
    line(ax, [(107, R2), (109, R2)], label="жоқ", lpos=(108, R2 + 2.6))
    line(ax, [(131, R2), (134, R2)], both=True, dashed=True)
    line(ax, [(120, R2 - 5.5), (120, R2 - 7.9)])

    process(ax, X[0], R3, "Шайқасты\nдайындау: белгілер,\nқор, ИИ шегі")
    inout(ax, X[1], R3, "Енгізу: A/D,\nJ/K/L, 1–3\n(буфер 6 кадр)")
    process(ax, X[2], R3, "Кадр 60 Гц:\nFSM, hitbox,\nпарирлеу, hitstop")
    decision(ax, X[3], R3, "Шайқас\nаяқталды\nма?")
    connector(ax, 111.5, R3, "3")
    internal(ax, X[5], R3, "Марков\nжиілік кестесі\n(ИИ)")
    line(ax, [(95, R2 - 7), (95, 71), (14, 71), (14, R3 + 5.5)], label="иә", lpos=(60, 71))
    line(ax, [(31, R3), (34, R3)])
    line(ax, [(56, R3), (59, R3)])
    line(ax, [(81, R3), (83, R3)])
    line(ax, [(95, R3 - 7), (95, 53.5), (45, 53.5), (45, R3 - 5.5)], label="жоқ", lpos=(75, 53.5))
    line(ax, [(107, R3), (108.9, R3)], label="иә", lpos=(107.6, R3 + 2.6))
    line(ax, [(70, R3 - 5.5), (70, 51), (145, 51), (145, R3 - 5.5)], both=True, dashed=True,
         label="кесте жаңарады / болжам", lpos=(112, 51))

    connector(ax, 3.2, R4, "3")
    process(ax, X[0], R4, "Нәтиже:\nқайтару → saved,\nөлтіру → killed")
    decision(ax, X[1], R4, "Түннің\nшайқасы\nбітті ме?")
    popup(ax, X[2], R4, "Түн\nқорытындысы")
    cylinder(ax, X[3], R4, "Автосақтау\n(save.json)")
    decision(ax, X[4], R4, "Түн < 3?")
    connector(ax, 145, R4, "2")
    connector(ax, 45, R4 - 11, "1")
    line(ax, [(5.8, R4), (9, R4)])
    line(ax, [(31, R4), (33, R4)])
    line(ax, [(57, R4), (59, R4)], label="иә", lpos=(58, R4 + 2.6))
    line(ax, [(45, R4 - 7), (45, R4 - 8.1)], label="жоқ", lpos=(49, R4 - 8.2))
    line(ax, [(81, R4), (84, R4)])
    line(ax, [(106, R4), (108, R4)])
    line(ax, [(132, R4), (142.4, R4)], label="иә", lpos=(137, R4 + 2.6))

    document(ax, X[3], R5, "Финал: құтқарылған\nсаны → 4 финалдың\nбірі")
    terminator(ax, X[4] + 1, R5, "Аяқтау:\nмәзірге оралу")
    line(ax, [(120, R4 - 7), (120, 29), (95, 29), (95, R5 + 5.5)], label="жоқ", lpos=(108, 29))
    line(ax, [(106, R5), (109, R5)])

    txt(ax, 80, 6, "1 — жүру (explore) циклына оралу;   2 — келесі түнді бастау;   "
                   "3 — шайқас нәтижесіне өту", size=7.2)
    fig.savefig(path)
    plt.close(fig)


# ---------- құрылымдық сызба ----------
STRUCT = [
    ("core\n(ядро)", ["game.py", "scene.py", "input.py", "assets.py", "save.py",
                       "audio.py", "audio_synth.py", "text.py"]),
    ("story\n(сюжет)", ["graph.py", "flags.py", "journal.py", "catalog.py"]),
    ("explore\n(жүру)", ["player.py", "locations.py"]),
    ("combat\n(жекпе-жек)", ["fighter.py", "fight.py", "hitbox.py", "setup.py",
                              "ai_scripted.py", "ai/markov.py", "ai/adaptive.py",
                              "ai/bots.py", "ai/metrics.py"]),
    ("render\n(сызу)", ["scenery.py", "lighting.py", "particles.py", "silhouette.py",
                         "portrait.py", "fighter_draw.py", "effects.py", "corruption.py", "ui.py"]),
    ("scenes\n(сахналар)", ["menu.py", "explore.py", "dialogue.py", "fight.py", "night_end.py"]),
    ("data\n(JSON)", ["night1.json", "night2.json", "night3.json", "locations.json",
                      "moves.json", "strings_kk.json", "endings.json"]),
]


def structural(path):
    fig = plt.figure(figsize=(8.27, 11.69), dpi=200)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 141)
    ax.axis("off")
    process(ax, 50, 134.5, "«Көлеңке» ойыны\nmain.py: кіру нүктесі, --selftest", w=44, h=8)

    def column(cx, top, title, items, w):
        process(ax, cx, top, title, w=w, h=8)
        y = top - 4.0
        for name in items:
            y -= 5.4
            process(ax, cx, y, name, w=w - 3, h=4.4)
        return y

    xs1 = [13, 38, 63, 88]
    xs2 = [18, 50, 82]
    line(ax, [(50.5, 130.5), (50.5, 128)], arrow=False)
    line(ax, [(xs1[0], 128), (xs1[-1], 128)], arrow=False)
    for cx, (t, it) in zip(xs1, STRUCT[:4]):
        line(ax, [(cx, 128), (cx, 126)], arrow=False)
        column(cx, 122, t, it, 22.5)
    # 2-қатар: ортадағы бос жолақпен (x=50.5) тізбектеледі
    line(ax, [(50.5, 128), (50.5, 66)], arrow=False, dashed=True)
    line(ax, [(xs2[0], 66), (xs2[-1], 66)], arrow=False)
    for cx, (t, it) in zip(xs2, STRUCT[4:]):
        line(ax, [(cx, 66), (cx, 64)], arrow=False)
        column(cx, 60, t, it, 26)
    txt(ax, 50, 2.5, "Тәуелділік бағыты: scenes → (core, story, explore, combat, render) → data.  "
                     "tools/: experiment.py, screenshots.py, make_figures.py", size=6.8)
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "docs" / "report" / "img"
    out.mkdir(parents=True, exist_ok=True)
    structural(out / "scheme_structural.png")
    functional(out / "scheme_functional.png")
    print("saved schemes to", out)
