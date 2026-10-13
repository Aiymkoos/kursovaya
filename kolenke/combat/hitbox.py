"""Hitbox / hurtbox: тік жазықтықтағы тіктөртбұрыштар (әлем координатасы)."""
import pygame

GROUND = 640
HURT_W = 50
HURT_H = 165


def hurtbox(x):
    """Кейіпкер денесі (қорғалатын аймақ)."""
    return pygame.Rect(int(x - HURT_W / 2), GROUND - HURT_H, HURT_W, HURT_H)


def hitbox(x, facing, move):
    """Соққы аймағы: move['reach']=[алыстық басы, ұзындығы], hit_y=[төмен, жоғары биіктік]."""
    start, length = move["reach"]
    y_lo, y_hi = move["hit_y"]
    near = x + facing * start
    far = near + facing * length
    left, right = min(near, far), max(near, far)
    return pygame.Rect(int(left), GROUND - y_hi, int(right - left), y_hi - y_lo)
