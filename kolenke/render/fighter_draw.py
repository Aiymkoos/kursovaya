"""Жауынгерді күйі мен кадрына қарай сызу (поза — moves.json ішіндегі 'arm' кілттері)."""
import math

from kolenke.combat.hitbox import GROUND
from kolenke.render.silhouette import draw_silhouette

FLASH_COLOR = (235, 235, 248)


def _lerp(a, b, t):
    return a + (b - a) * t


def pose(f):
    """(arm_angle, lean, weapon_len) — жауынгердің қазіргі позасы."""
    weapon = 28.0 if f.spec.get("weapon") else 0.0
    base_arm = 0.45 if weapon else None
    s = f.state
    m = f.move
    if m:
        a0, a1, a2, a3 = m["arm"]
        su, ac, rec = m["startup"], m["active"], m["recovery"]
        lean_wind = m.get("lean", -8)
        weapon = m.get("weapon_len", weapon)
        if f.frame < su:
            t = f.frame / su
            t = t * t * (3 - 2 * t)      # ease: қозғалыс «дайындалады»
            return _lerp(a0, a1, t), lean_wind * t, weapon
        if f.frame < su + ac:
            return a2, 14.0, weapon
        t = (f.frame - su - ac) / max(1, rec)
        return _lerp(a2, a3, t), 14.0 * (1 - t), weapon
    if s == "block":
        return 2.3, -4.0, weapon
    if s == "hurt":
        return base_arm, -16.0, weapon
    if s == "stagger":
        return 0.2, -22.0, weapon
    if s == "dead":
        return base_arm, -48.0, 0.0
    return base_arm, 0.0, weapon


def draw_fighter(surface, f, accent, t, part="all", detail=1.0):
    """Қайтарады: (қол, ұш) — соққы ізі (trail) үшін."""
    arm, lean, weapon = pose(f)
    lean += math.sin(t * 2.2 + (0 if f.facing > 0 else 1.3)) * 1.5
    swing = math.sin(f.walk_phase * 2) * 0.8 if f.walking else 0.0
    return draw_silhouette(
        surface, f.x, GROUND, accent, f.facing, swing, t=t, part=part,
        detail=0.0 if f.state == "dead" else detail,
        arm_angle=arm, lean=lean, weapon=weapon,
        body_color=FLASH_COLOR if f.flash > 0 else None)
