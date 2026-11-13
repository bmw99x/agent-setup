"""Parse the Mermaid blocks of a markdown file into one graph of nodes and edges.

Handles `flowchart`/`graph` (node shapes, chained links, `&`, `|label|` and `-- label -->` links, subgraphs,
`class`/`:::`/`classDef`) and `sequenceDiagram` (participants, `box`, solid-arrow messages; dashed replies are
ignored). Nodes from different blocks that share an id or a label are merged, so an overview plus a detail
diagram count as one map.
"""

import re
from collections import deque
from dataclasses import dataclass, field

FENCE = re.compile(r"```\s*mermaid[^\n]*\n(.*?)```", re.S | re.I)
NODE_ID = re.compile(r"\w+(?:-\w+)*")
LINK_TEXT = re.compile(r"\s*(<)?(--|==|-\.)\s+(.+?)\s+(-{2,}>|={2,}>|\.-+>|-{3,}|={3,}|\.-|-{2,}[ox]|={2,}[ox])")
LINK_PLAIN = re.compile(r"\s*(<)?(-{2,}|={2,}|-\.+-|~{3,})(>|o\b|x\b)?")
PIPE = re.compile(r"\s*\|([^|]*)\|")
SEQ_ARROW = re.compile(r"^\s*([^\s\-+>:][^:]*?)\s*(--?>>|--?>|--?x|--?\))\s*[+-]?\s*([^:]+?)\s*:\s*(.*)$")
SEQ_KEYWORDS = ("note", "loop", "alt", "opt", "par", "rect", "else", "and", "critical", "break", "activate",
                "deactivate", "autonumber", "title", "create", "destroy", "link", "links")


@dataclass
class Node:
    key: str
    label: str = ""
    tags: list = field(default_factory=list)  # subgraph / box titles and class names around the node

    @property
    def text(self):
        return f"{self.key.split(':', 1)[-1]} {self.label}".strip()


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    dotted: bool = False
    seq: bool = False


class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.blocks = []
        self._parent = {}

    # ---- union-find so blocks share nodes by id or label
    def _find(self, k):
        while self._parent.get(k, k) != k:
            k = self._parent[k]
        return k

    def canonical(self, k):
        return self._find(k)

    def finish(self):
        """Merge nodes of different blocks that share a label, or share an id with no conflicting label."""
        norm = {k: re.sub(r"\W+", " ", n.label).strip().lower() for k, n in self.nodes.items()}
        keys = list(self.nodes)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                if a.split(":", 1)[0] == b.split(":", 1)[0]:
                    continue
                same_label = norm[a] and norm[a] == norm[b]
                same_id = a.split(":", 1)[1] == b.split(":", 1)[1] and (not norm[a] or not norm[b] or norm[a] == norm[b])
                if same_label or same_id:
                    self._parent[self._find(b)] = self._find(a)
        merged = {}
        for key, node in self.nodes.items():
            target = merged.setdefault(self._find(key), Node(self._find(key)))
            if node.label and node.label not in target.label:
                target.label = f"{target.label} | {node.label}" if target.label else node.label
            target.tags.extend(t for t in node.tags if t not in target.tags)
        self.nodes = merged
        for e in self.edges:
            e.src, e.dst = self._find(e.src), self._find(e.dst)

    # ---- queries
    def matching(self, include, exclude=None):
        inc = re.compile(include, re.I)
        exc = re.compile(exclude, re.I) if exclude else None
        return {k for k, n in self.nodes.items() if inc.search(n.text) and not (exc and exc.search(n.text))}

    def adjacent(self, a_keys, b_keys):
        return [e for e in self.edges if (e.src in a_keys and e.dst in b_keys) or (e.src in b_keys and e.dst in a_keys)]

    def path(self, src_keys, dst_keys, dst_label=None, max_hops=4, blocked=frozenset()):
        """Directed path src -> dst of at most max_hops edges whose inner nodes are not in `blocked`.
        For sequence messages, the last hop may also hit dst through its message text (`dst_label`)."""
        label_re = re.compile(dst_label, re.I) if dst_label else None
        queue = deque((k, 0) for k in src_keys)
        seen = set(src_keys)
        if src_keys & dst_keys:
            return True
        while queue:
            node, hops = queue.popleft()
            if hops >= max_hops:
                continue
            for e in self.edges:
                if e.src != node:
                    continue
                if e.dst in dst_keys or (e.seq and label_re and label_re.search(e.label)):
                    return True
                if e.dst in seen or e.dst in blocked:
                    continue
                seen.add(e.dst)
                queue.append((e.dst, hops + 1))
        return False

    def reachable(self, src_keys, max_hops=12):
        seen = set(src_keys)
        frontier = list(src_keys)
        for _ in range(max_hops):
            nxt = []
            for e in self.edges:
                if e.src in frontier and e.dst not in seen:
                    seen.add(e.dst)
                    nxt.append(e.dst)
            frontier = nxt
        return seen

    def layer_text(self, key, strip=None):
        """Text that tags a node with a layer: enclosing subgraph/box titles, classes, and whatever the label
        says beyond the symbol name itself (`strip`)."""
        node = self.nodes[key]
        rest = node.label
        if strip:
            rest = re.sub(strip, " ", rest, flags=re.I)
        return " ".join(node.tags + [rest])


def _label_of(raw):
    raw = raw.strip()
    raw = re.sub(r"^[\[\(\{>/\\]+|[\]\)\}/\\]+$", "", raw).strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        raw = raw[1:-1]
    raw = raw.replace("<br/>", " ").replace("<br>", " ").replace("#quot;", '"')
    raw = re.sub(r"<[^>]+>", " ", raw)
    return raw.strip()


MIRROR = {"[": "]", "(": ")", "{": "}", "/": "/", "\\": "\\"}


def _read_shape(s, i):
    """At s[i] a shape opener such as `[`, `([`, `[(`, `{{`, `>`; return (label, end_index)."""
    if s[i] == ">":
        close = s.find("]", i + 1)
        close = len(s) - 1 if close < 0 else close
        return _label_of(s[i + 1:close]), close + 1
    j = i
    while j < len(s) and s[j] in "[({/\\" and j - i < 2:
        j += 1
    opener = s[i:j]
    content_start = j
    k = j
    if k < len(s) and s[k] == '"':
        q = s.find('"', k + 1)
        k = q + 1 if q > 0 else len(s)
    closing = "".join(MIRROR[c] for c in reversed(opener))
    pos = s.find(closing, k)
    if pos < 0:
        pos = s.find(MIRROR[opener[0]], k)
        closing = MIRROR[opener[0]]
    if pos < 0:
        return _label_of(s[content_start:]), len(s)
    return _label_of(s[content_start:pos]), pos + len(closing)


class _FlowParser:
    def __init__(self, graph, prefix):
        self.g = graph
        self.prefix = prefix
        self.stack = []  # subgraph titles
        self.class_of = {}

    def key(self, ident):
        return f"{self.prefix}:{ident}"

    def touch(self, ident, label=None):
        k = self.key(ident)
        node = self.g.nodes.setdefault(k, Node(k, ""))
        if label:
            node.label = label
        node.tags.extend(t for t in self.stack if t not in node.tags)
        return k

    def node_group(self, s, i):
        keys = []
        while True:
            while i < len(s) and s[i] == " ":
                i += 1
            m = NODE_ID.match(s, i)
            if not m:
                return keys, i
            ident = m.group(0)
            if ident == "end" and not keys:
                return keys, i
            i = m.end()
            label = None
            if i < len(s) and s[i] == "@" and i + 1 < len(s) and s[i + 1] == "{":
                close = s.find("}", i)
                body = s[i + 2:close if close > 0 else len(s)]
                lm = re.search(r"label\s*:\s*\"([^\"]*)\"", body)
                label = lm.group(1) if lm else None
                i = close + 1 if close > 0 else len(s)
            elif i < len(s) and s[i] in "[({>":
                label, i = _read_shape(s, i)
            k = self.touch(ident, label)
            if s.startswith(":::", i):
                cm = re.match(r":::([\w-]+)", s[i:])
                self.g.nodes[k].tags.append(cm.group(1))
                i += cm.end()
            keys.append(k)
            j = i
            while j < len(s) and s[j] == " ":
                j += 1
            if j < len(s) and s[j] == "&":
                i = j + 1
                continue
            return keys, i

    def link(self, s, i):
        m = LINK_TEXT.match(s, i)
        if m:
            return m.group(3).strip().strip('"'), "." in (m.group(2) + m.group(4)), m.end()
        m = LINK_PLAIN.match(s, i)
        if not m or (m.group(2).startswith("-") and len(m.group(2)) < 2):
            return None
        end = m.end()
        label = ""
        pm = PIPE.match(s, end)
        if pm:
            label, end = pm.group(1).strip().strip('"'), pm.end()
        return label, "." in m.group(2), end

    def statement(self, s):
        s = s.strip().rstrip(";")
        if not s:
            return
        low = s.lower()
        if re.match(r"(flowchart|graph)\b", low):
            return
        if low.startswith("subgraph"):
            rest = s[len("subgraph"):].strip()
            m = re.match(r"(\w[\w-]*)\s*\[(.*)\]\s*$", rest)
            title = f"{m.group(1)} {_label_of(m.group(2))}" if m else _label_of(rest)
            self.stack.append(title)
            return
        if low == "end":
            if self.stack:
                self.stack.pop()
            return
        if low.startswith(("classdef", "style ", "linkstyle", "click ", "direction ", "%%")):
            return
        if low.startswith("class "):
            parts = s.split()
            if len(parts) >= 3:
                for ident in parts[1].split(","):
                    k = self.touch(ident.strip())
                    self.g.nodes[k].tags.append(parts[2])
            return
        groups, i = self.node_group(s, 0)
        if not groups:
            return
        while True:
            lk = self.link(s, i)
            if not lk:
                break
            label, dotted, i = lk
            nxt, i = self.node_group(s, i)
            if not nxt:
                break
            for a in groups:
                for b in nxt:
                    self.g.edges.append(Edge(a, b, label, dotted))
            groups = nxt

    def parse(self, body):
        for line in body.splitlines():
            line = re.sub(r"%%.*$", "", line)
            for stmt in re.split(r";(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", line):
                self.statement(stmt)


class _SeqParser:
    def __init__(self, graph, prefix):
        self.g = graph
        self.prefix = prefix
        self.box = []
        self.blocks = []  # (kind, condition) of open alt/opt/loop/par/critical/rect blocks

    def touch(self, ident, label=None):
        ident = ident.strip().strip('"')
        k = f"{self.prefix}:{ident}"
        node = self.g.nodes.setdefault(k, Node(k, ""))
        if label:
            node.label = label
        node.tags.extend(t for t in self.box if t not in node.tags)
        return k

    def parse(self, body):
        for line in body.splitlines():
            line = re.sub(r"%%.*$", "", line).strip()
            low = line.lower()
            if not line or low.startswith("sequencediagram"):
                continue
            m = re.match(r"(participant|actor)\s+(.+?)(?:\s+as\s+(.+))?$", line, re.I)
            if m:
                self.touch(m.group(2), _label_of(m.group(3) or ""))
                continue
            if low.startswith("box"):
                colour = r"rgba?\([^)]*\)|#\w+|transparent|aqua|purple|gr[ae]y|light\w+|white|black|red|green|blue|yellow|orange|pink"
                self.box.append(re.sub(rf"^box\s+(?:(?:{colour})(?=\s|$))?\s*", "", line, flags=re.I) or "box")
                continue
            word = low.split(" ")[0]
            if low == "end":
                if self.blocks:
                    self.blocks.pop()
                elif self.box:
                    self.box.pop()
                continue
            if word in ("alt", "opt", "loop", "par", "critical", "break", "rect"):
                self.blocks.append(line[len(word):].strip())
                continue
            if word in ("else", "and", "option") and self.blocks:
                self.blocks[-1] = line[len(word):].strip()
                continue
            if word in SEQ_KEYWORDS:
                continue
            m = SEQ_ARROW.match(line)
            if m:
                a, arrow, b, msg = m.groups()
                ka, kb = self.touch(a), self.touch(b.lstrip("+-"))
                if not arrow.startswith("--"):
                    conditions = " ".join(f"[{c}]" for c in self.blocks if c)
                    self.g.edges.append(Edge(ka, kb, f"{msg.strip()} {conditions}".strip(), False, seq=True))


def parse_markdown(text):
    g = Graph()
    for n, body in enumerate(FENCE.findall(text)):
        g.blocks.append(body)
        first = next((ln.strip().lower() for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("%%")), "")
        prefix = f"b{n}"
        if first.startswith("sequencediagram"):
            _SeqParser(g, prefix).parse(body)
        elif first.startswith(("flowchart", "graph")):
            _FlowParser(g, prefix).parse(body)
    g.finish()
    return g
