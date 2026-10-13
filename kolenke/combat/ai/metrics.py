"""Болжау дәлдігін өлшеу және базалық әдістермен салыстыру."""
import random
from collections import Counter

from kolenke.combat.ai.markov import ACTIONS, MarkovPredictor


def online_accuracy(sequence, predictor):
    """Тізбекті бір-бірлеп беріп, әр қадамдағы болжам дәлдігін есептейді."""
    hits = total = 0
    curve = []
    for a in sequence:
        pred, _ = predictor.predict()
        if pred is not None:
            total += 1
            hits += pred == a
            curve.append(hits / total)
        predictor.observe(a)
    return (hits / total if total else 0.0), curve


def baseline_random(sequence, seed=0):
    rng = random.Random(seed)
    if len(sequence) < 2:
        return 0.0
    return sum(rng.choice(ACTIONS) == a for a in sequence[1:]) / (len(sequence) - 1)


def baseline_last(sequence):
    """Алдыңғы әрекет қайталанады деп болжау."""
    if len(sequence) < 2:
        return 0.0
    return sum(sequence[i - 1] == sequence[i] for i in range(1, len(sequence))) / (len(sequence) - 1)


def baseline_frequency(sequence):
    """Әрқашан бұрынғы ең жиі әрекетті болжау (order-0)."""
    seen, hits, total = Counter(), 0, 0
    for a in sequence:
        if seen:
            total += 1
            hits += seen.most_common(1)[0][0] == a
        seen[a] += 1
    return hits / total if total else 0.0


def compare(sequence):
    """Барлық әдістің дәлдігі бір сөздікте."""
    return {
        "random": baseline_random(sequence),
        "last": baseline_last(sequence),
        "frequency": baseline_frequency(sequence),
        "markov1": online_accuracy(sequence, MarkovPredictor(order=1))[0],
        "markov2": online_accuracy(sequence, MarkovPredictor(order=2))[0],
        "markov3": online_accuracy(sequence, MarkovPredictor(order=3))[0],
    }
