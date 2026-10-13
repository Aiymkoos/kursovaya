"""Диалог графы: түйіндер мен таңдау бұтақтары (JSON-нан жүктеледі).

Түйін өрістері: speaker, text, next | choices | end,
set ({флаг: мән}), memory (журналға жазба id).
Таңдау өрістері: text, next, set, memory, requires ({флаг: мән}).
"""
import json


class GraphError(Exception):
    pass


class DialogueGraph:
    def __init__(self, data):
        self.id = data.get("id", "")
        self.start = data["start"]
        self.nodes = data["nodes"]
        self.speakers = data.get("speakers", {})
        self.memories = data.get("memories", {})
        self.validate()

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def targets(self, node):
        """Түйіннен шығатын барлық өтулер."""
        out = []
        if "next" in node:
            out.append(node["next"])
        out += [c["next"] for c in node.get("choices", [])]
        return out

    def validate(self):
        if self.start not in self.nodes:
            raise GraphError(f"Бастапқы түйін жоқ: {self.start}")
        for nid, node in self.nodes.items():
            ends = [k for k in ("next", "choices", "end") if k in node]
            if len(ends) != 1:
                raise GraphError(f"{nid}: next/choices/end біреуі ғана болу керек")
            for t in self.targets(node):
                if t not in self.nodes:
                    raise GraphError(f"{nid}: белгісіз түйінге өту: {t}")
            for mem in self._memory_refs(node):
                if mem not in self.memories:
                    raise GraphError(f"{nid}: белгісіз естелік: {mem}")
            if node.get("speaker") and node["speaker"] not in self.speakers:
                raise GraphError(f"{nid}: белгісіз кейіпкер: {node['speaker']}")
        unreachable = set(self.nodes) - self.reachable()
        if unreachable:
            raise GraphError(f"Қол жетпейтін түйіндер: {sorted(unreachable)}")

    def _memory_refs(self, node):
        refs = [node["memory"]] if "memory" in node else []
        refs += [c["memory"] for c in node.get("choices", []) if "memory" in c]
        return refs

    def reachable(self):
        seen, stack = set(), [self.start]
        while stack:
            nid = stack.pop()
            if nid in seen:
                continue
            seen.add(nid)
            stack += self.targets(self.nodes[nid])
        return seen


class DialogueRunner:
    """Графпен жүру: түйінге кіргенде флагтар мен журнал жаңарады."""

    def __init__(self, graph, flags, journal):
        self.graph = graph
        self.flags = flags
        self.journal = journal
        self.node_id = None
        self._enter(graph.start)

    @property
    def node(self):
        return self.graph.nodes[self.node_id]

    @property
    def finished(self):
        return "end" in self.node

    def _apply(self, spec):
        for k, v in spec.get("set", {}).items():
            self.flags.set(k, v)
        if "memory" in spec:
            self.journal.add(spec["memory"])

    def _enter(self, node_id):
        self.node_id = node_id
        self._apply(self.node)

    def choices(self):
        """Қазіргі шарттарға сай көрінетін таңдаулар (түпнұсқа индекс, мәтін)."""
        return [
            (i, c) for i, c in enumerate(self.node.get("choices", []))
            if self.flags.check(c.get("requires"))
        ]

    @property
    def has_choices(self):
        return "choices" in self.node

    def advance(self):
        """Таңдауы жоқ түйіннен келесіге өту."""
        if self.finished or self.has_choices:
            return False
        self._enter(self.node["next"])
        return True

    def choose(self, visible_index):
        """visible_index — көрінетін тізімдегі 0-негізді нөмір."""
        visible = self.choices()
        if not self.has_choices or not 0 <= visible_index < len(visible):
            return False
        choice = visible[visible_index][1]
        self._apply(choice)
        self._enter(choice["next"])
        return True
