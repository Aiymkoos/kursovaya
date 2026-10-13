"""Жатақхана локациялары: JSON-нан жүктеледі және тексеріледі."""
import json
from dataclasses import dataclass, field


class LocationError(Exception):
    pass


@dataclass
class Obj:
    id: str
    kind: str          # "door" | "npc"
    x: int
    w: int
    label: str         # strings_kk.json кілті
    to: str = ""
    spawn: int = 0
    dialogue: str = ""
    night: int = 0          # 0 — әрқашан белсенді; N — тек N-түнде
    who: str = ""           # NPC кейіпкер id (флагтар: <who>_saved/_killed)
    fight: str = ""         # "darkhan" немесе "@флаг1,флаг2" (ретпен шайқас)
    accent: tuple = (230, 230, 230)

    @property
    def done_flag(self):
        """Диалог аяқталғанда қойылатын флаг атауы."""
        return self.dialogue.replace(".json", "") + "_talk_done"

    def active(self, night):
        return self.night in (0, night)

    def enemies(self, flags):
        """Осы NPC-мен өтетін шайқастар тізімі (диалогтан кейін анықталады)."""
        if not self.fight:
            return []
        if self.fight.startswith("@"):
            names = [flags.get(k, "") for k in self.fight[1:].split(",")]
            return [n for n in names if n]
        return [self.fight]


@dataclass
class Location:
    id: str
    width: int
    name: str
    start: int
    objects: list = field(default_factory=list)


def load_locations(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    locs = {}
    for lid, d in raw.items():
        objs = []
        for o in d["objects"]:
            o = dict(o)
            if "accent" in o:
                o["accent"] = tuple(o["accent"])
            objs.append(Obj(**o))
        locs[lid] = Location(lid, d["width"], d["name"], d["start"], objs)
    _validate(locs)
    return locs


def _validate(locs):
    for loc in locs.values():
        for o in loc.objects:
            if not 0 <= o.x <= loc.width:
                raise LocationError(f"{loc.id}/{o.id}: x локациядан тыс")
            if o.kind == "door":
                if o.to not in locs:
                    raise LocationError(f"{loc.id}/{o.id}: белгісіз есік: {o.to}")
                if not 0 <= o.spawn <= locs[o.to].width:
                    raise LocationError(f"{loc.id}/{o.id}: spawn локациядан тыс")
            elif o.kind == "npc":
                if not o.dialogue:
                    raise LocationError(f"{loc.id}/{o.id}: диалог файлы жоқ")
            else:
                raise LocationError(f"{loc.id}/{o.id}: белгісіз түр: {o.kind}")
