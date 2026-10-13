"""Диалог таңдауларын (флагтар, журнал) жекпе-жек параметрлеріне айналдыру."""
from kolenke.combat.fighter import load_combat_data

START_MEMORY_FRACTION = 0.5   # жекпе-жек басында естелік жолағы = қордың жартысы
CALLED_NAME_HP_MULT = 0.85    # атын атаған жаудың күші азаяды
RESTORE_RESERVE_COST = 25     # адамды қайтару келесі түндегі қорды азайтады


def known_tells(data, enemy, flags):
    """Қарсылас қимылдарының ішінде ойыншы танитындарының id-лері."""
    moves = data["fighters"][enemy]["moves"]
    return {m for m in moves
            if not data["moves"][m].get("tell_flag") or flags.get(data["moves"][m]["tell_flag"])}


def journal_entries_for(journal, who):
    return sum(1 for _, mem in journal.entries() if mem["who"] == who)


def fight_params(flags, journal, reserve, enemy, data=None):
    """Fight(...) конструкторына берілетін параметрлер сөздігі."""
    data = data or load_combat_data()
    return dict(
        known_tells=known_tells(data, enemy, flags),
        start_memory=reserve * START_MEMORY_FRACTION,
        enemy_hp_mult=CALLED_NAME_HP_MULT if flags.get(enemy + "_called_name") else 1.0,
        entries=journal_entries_for(journal, enemy),
    )
