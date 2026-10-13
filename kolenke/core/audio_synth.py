"""Дыбыс синтезі: сыртқы файлсыз, математика арқылы (22050 Гц, 16 бит, моно).

Әр функция bytes қайтарады — pygame.mixer.Sound(buffer=...) қабылдайды.
"""
import math
import random
from array import array

RATE = 22050
PEAK = 32767


def _pack(samples, gain=1.0):
    out = array("h")
    for v in samples:
        out.append(int(max(-1.0, min(1.0, v * gain)) * PEAK * 0.9))
    return out.tobytes()


def _n(duration):
    return int(RATE * duration)


def _noise(rng):
    return rng.uniform(-1.0, 1.0)


def hit(heavy=False, seed=1):
    rng = random.Random(seed)
    dur = 0.34 if heavy else 0.2
    f0 = 70 if heavy else 120
    return _pack((math.sin(2 * math.pi * f0 * (1 - 0.5 * i / _n(dur)) * i / RATE)
                  * math.exp(-i / RATE * (14 if heavy else 26)) * 0.9
                  + _noise(rng) * math.exp(-i / RATE * 45) * 0.7
                  for i in range(_n(dur))))


def block(seed=2):
    rng = random.Random(seed)
    return _pack((sum(math.sin(2 * math.pi * f * i / RATE) for f in (610, 905, 1230)) / 3
                  * math.exp(-i / RATE * 14) * 0.7 + _noise(rng) * math.exp(-i / RATE * 90) * 0.5
                  for i in range(_n(0.28))))


def parry(seed=3):
    rng = random.Random(seed)
    dur = 0.8
    return _pack((sum(math.sin(2 * math.pi * f * i / RATE) * a
                      for f, a in ((1240, 1.0), (1860, 0.7), (2480, 0.5), (3100, 0.3))) / 2.5
                  * math.exp(-i / RATE * 5) * 0.8
                  + math.sin(2 * math.pi * 58 * i / RATE) * math.exp(-i / RATE * 12) * 0.7
                  + _noise(rng) * math.exp(-i / RATE * 60) * 0.4
                  for i in range(_n(dur))))


def whoosh(rise=True, dur=0.28, seed=4):
    rng = random.Random(seed)
    n = _n(dur)
    lp = 0.0
    out = []
    for i in range(n):
        k = i / n
        env = math.sin(math.pi * k) ** 2
        a = 0.05 + 0.35 * (k if rise else 1 - k)
        lp += (_noise(rng) - lp) * a
        out.append(lp * env * 1.6)
    return _pack(out)


def chime(notes=(523.25, 659.25, 783.99), seed=5):
    n = _n(1.1)
    out = []
    for i in range(n):
        t = i / RATE
        v = 0.0
        for k, f in enumerate(notes):
            tt = t - k * 0.09
            if tt > 0:
                v += math.sin(2 * math.pi * f * tt) * math.exp(-tt * 3.2)
        out.append(v / len(notes) * 1.3)
    return _pack(out)


def boom(seed=6):
    rng = random.Random(seed)
    return _pack((math.sin(2 * math.pi * 48 * (1 - 0.3 * i / _n(1.0)) * i / RATE)
                  * math.exp(-i / RATE * 4) * 0.95
                  + _noise(rng) * math.exp(-i / RATE * 10) * 0.4 for i in range(_n(1.0))))


def swell(seed=7):
    """Көлеңке жұту кезіндегі баяу төмен дыбыс."""
    rng = random.Random(seed)
    n = _n(1.4)
    lp = 0.0
    out = []
    for i in range(n):
        k = i / n
        env = math.sin(math.pi * k) ** 1.5
        lp += (_noise(rng) - lp) * 0.04
        out.append((lp * 2.2 + math.sin(2 * math.pi * 55 * i / RATE) * 0.5
                    + math.sin(2 * math.pi * 82 * i / RATE) * 0.3) * env * 0.8)
    return _pack(out)


def tick(low=False, seed=8):
    """Метроном: жоғары «тік» немесе төмен «так»."""
    rng = random.Random(seed)
    f = 1050 if low else 1750
    return _pack((math.sin(2 * math.pi * f * i / RATE) * math.exp(-i / RATE * 70) * 0.8
                  + _noise(rng) * math.exp(-i / RATE * 220) * 0.5 for i in range(_n(0.12))))


def drum(seed=9):
    rng = random.Random(seed)
    n = _n(0.4)
    return _pack((math.sin(2 * math.pi * (95 - 45 * min(1.0, i / (RATE * 0.12))) * i / RATE)
                  * math.exp(-i / RATE * 12) * 0.95
                  + _noise(rng) * math.exp(-i / RATE * 60) * 0.35 for i in range(n)))


def knife(seed=10):
    rng = random.Random(seed)
    n = _n(0.45)
    out = []
    for i in range(n):
        t = i / RATE
        scrape = _noise(rng) * min(1.0, t * 12) * math.exp(-t * 14) * 0.5
        ping = (math.sin(2 * math.pi * 2350 * t) + 0.6 * math.sin(2 * math.pi * 3480 * t)) / 1.6
        out.append(scrape + ping * math.exp(-t * 9) * 0.55 * (1 if t > 0.03 else 0))
    return _pack(out)


def stitch(seed=11):
    """Тігін машинасы: тез-тез шертулер."""
    rng = random.Random(seed)
    n = _n(0.55)
    out = [0.0] * n
    step = _n(0.045)
    for c in range(12):
        s = c * step
        for j in range(_n(0.02)):
            if s + j < n:
                out[s + j] += (_noise(rng) * 0.6 + math.sin(2 * math.pi * 1500 * j / RATE) * 0.4) \
                    * math.exp(-j / RATE * 180)
    return _pack(out)


def click(seed=12):
    return _pack((math.sin(2 * math.pi * 880 * i / RATE) * math.exp(-i / RATE * 120) * 0.6
                  for i in range(_n(0.06))))


def blizzard(duration=4.0, seed=13):
    """Үзіліссіз қайталанатын боран шуы (соңы басымен біріктіріледі)."""
    rng = random.Random(seed)
    n, m = _n(duration), _n(0.25)
    raw = []
    lp1 = lp2 = 0.0
    for i in range(n + m):
        lp1 += (_noise(rng) - lp1) * 0.10
        lp2 += (_noise(rng) - lp2) * 0.012
        gust = 0.65 + 0.35 * math.sin(2 * math.pi * 2 * i / (RATE * duration))
        raw.append((lp1 * 0.9 + lp2 * 4.0) * gust * 0.55)
    out = raw[:n]
    for i in range(m):      # тігіссіз қайталау үшін кросфейд
        w = i / m
        out[i] = raw[i] * w + raw[n + i] * (1 - w)
    return _pack(out)


SOUNDS = {
    "hit": lambda: hit(False), "heavy_hit": lambda: hit(True), "block": block,
    "parry": parry, "whoosh": whoosh, "whoosh_light": lambda: whoosh(True, 0.16),
    "chime": chime, "boom": boom, "swell": swell, "tick": lambda: tick(False),
    "tock": lambda: tick(True), "drum": drum, "knife": knife, "stitch": stitch,
    "click": click, "blizzard": blizzard,
}
