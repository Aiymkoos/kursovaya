"""Бейімделетін ИИ эксперименті: болжау дәлдігі және бейімделу әсері.

Іске қосу:  python tools/experiment.py --fights 30 --out docs/experiment
Нәтиже: CSV кестелер, сурет (PNG) және консольдегі қорытынды.
Бәрі seed бойынша қайталанады (бот: i, ИИ: 1000+i).
"""
import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from kolenke.combat.ai.adaptive import AdaptiveAI
from kolenke.combat.ai.bots import BOTS
from kolenke.combat.ai.metrics import compare
from kolenke.combat.ai_scripted import ScriptedAI
from kolenke.combat.fight import Fight

MAX_TICKS = 5400   # 90 секунд
METHODS = ("random", "last", "frequency", "markov1", "markov2", "markov3")


ENEMY = {"name": "bekzat"}


def run_fight(bot_cls, ai, bot_seed):
    f = Fight(ENEMY["name"], enemy_controller=ai, player_controller=bot_cls(seed=bot_seed))
    while not f.over and f.frame_no < MAX_TICKS:
        f.tick()
    return f


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def part_accuracy(n):
    """Әр бот үшін: әдістердің болжау дәлдігі (ИИ-мен жекпе-жек кезінде жиналған әрекеттер)."""
    rows, curves, in_fight = [], {}, {}
    for name, cls in BOTS.items():
        per_method = {m: [] for m in METHODS}
        live, curve_acc = [], []
        for i in range(n):
            ai = AdaptiveAI(seed=1000 + i, threshold=0.55)
            run_fight(cls, ai, i)
            seq = ai.predictor.history
            if len(seq) < 8:
                continue
            for m, v in compare(seq).items():
                per_method[m].append(v)
            live.append(ai.predictor.accuracy)
            # оқу қисығы: алғашқы 40 әрекет бойынша жылжымалы дәлдік
            hits = [p == a for p, a in ai.predictor.log][:40]
            curve_acc.append(hits)
        rows.append([name] + [round(mean(per_method[m]), 3) for m in METHODS]
                    + [round(mean(live), 3), len(live)])
        in_fight[name] = mean(live)
        L = max((len(h) for h in curve_acc), default=0)
        curves[name] = [mean(h[k] for h in curve_acc if len(h) > k) for k in range(L)]
    return rows, curves


def part_effect(n):
    """ИИ түрлері бойынша: ботқа қарсы нәтиже (скрипт vs бейімделетін)."""
    rows = []
    for name, cls in BOTS.items():
        for label, make in (("scripted", lambda i: ScriptedAI(seed=1000 + i)),
                            ("adaptive", lambda i: AdaptiveAI(seed=1000 + i, threshold=0.55))):
            lost, dealt, wins, dur, timeouts = [], [], 0, [], 0
            for i in range(n):
                f = run_fight(cls, make(i), i)
                lost.append(1 - f.player.hp / f.player.max_hp)
                dealt.append(1 - f.enemy.hp / f.enemy.max_hp)
                wins += f.over and f.winner is f.player
                timeouts += not f.over
                dur.append(f.frame_no / 60)
            rows.append([name, label, round(mean(lost), 3), round(mean(dealt), 3),
                         round(wins / n, 3), round(mean(dur), 1), timeouts])
    return rows


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def plot(out, acc_rows, curves, effect_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.2))
    width = 0.13
    for j, m in enumerate(METHODS):
        ax.bar([i + j * width for i in range(len(acc_rows))],
               [r[1 + j] for r in acc_rows], width, label=m)
    ax.set_xticks([i + width * 2.5 for i in range(len(acc_rows))])
    ax.set_xticklabels([r[0] for r in acc_rows])
    ax.axhline(1 / 3, color="gray", ls=":", lw=1)
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, 1.05)
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "accuracy.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.2))
    for name, ys in curves.items():
        w = 5
        sm = [mean(ys[max(0, k - w + 1):k + 1]) for k in range(len(ys))]
        ax.plot(range(1, len(sm) + 1), sm, label=name)
    ax.axhline(1 / 3, color="gray", ls=":", lw=1)
    ax.set_xlabel("observed player actions")
    ax.set_ylabel("accuracy (moving avg, 5)")
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "learning_curve.png", dpi=150)
    plt.close(fig)

    names = list(BOTS)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for j, label in enumerate(("scripted", "adaptive")):
        vals = [next(r[2] for r in effect_rows if r[0] == n and r[1] == label) for n in names]
        ax.bar([i + j * 0.38 for i in range(len(names))], vals, 0.38, label=label)
    ax.set_xticks([i + 0.19 for i in range(len(names))])
    ax.set_xticklabels(names)
    ax.set_ylabel("player HP lost (fraction)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "effect.png", dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fights", type=int, default=30)
    ap.add_argument("--out", default="docs/experiment")
    ap.add_argument("--enemy", default="bekzat", help="darkhan | zhanel | madina | bekzat")
    args = ap.parse_args()
    ENEMY["name"] = args.enemy
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    acc_rows, curves = part_accuracy(args.fights)
    write_csv(out / "accuracy.csv", ["bot", *METHODS, "ai_live_accuracy", "fights_used"], acc_rows)
    write_csv(out / "learning_curve.csv", ["bot", "step", "accuracy"],
              [[b, k + 1, round(v, 3)] for b, ys in curves.items() for k, v in enumerate(ys)])
    effect_rows = part_effect(args.fights)
    write_csv(out / "effect.csv", ["bot", "ai", "player_hp_lost", "enemy_hp_lost",
                                   "player_win_rate", "avg_seconds", "timeouts"], effect_rows)
    try:
        plot(out, acc_rows, curves, effect_rows)
    except ImportError:
        print("matplotlib жоқ: суреттер жасалмады")

    print("\n== Болжау дәлдігі (бот -> әдіс) ==")
    print("bot        " + " ".join(f"{m:>9}" for m in METHODS) + "   ai_live")
    for r in acc_rows:
        print(f"{r[0]:<10} " + " ".join(f"{v:9.3f}" for v in r[1:1 + len(METHODS)]) + f"   {r[-2]:.3f}")
    print("\n== Бейімделу әсері ==")
    print("bot        ai         hp_lost  enemy_lost  win_rate  sec  timeouts")
    for r in effect_rows:
        print(f"{r[0]:<10} {r[1]:<9} {r[2]:8.3f} {r[3]:11.3f} {r[4]:9.3f} {r[5]:5.1f} {r[6]:5d}")


if __name__ == "__main__":
    main()
