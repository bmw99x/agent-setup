"""Static call graph of Python packages, for the dependency explorer.

Usage:
    python3 -I callgraph.py --root <repo root> --package <dir> [--package <dir> ...]
                            [--entry <file>[::<substring>] ...] --out graph.json

--package   directory under --root whose every .py file is graphed (classes, methods, functions).
--entry     extra file whose top-level functions are graphed as entry points; with ::<substring>, only
            functions whose source contains it (e.g. cli.py::orders keeps the commands that touch orders).

Edges: "call" (a resolved call), "ref" (a resolved non-call use: partial(f), callbacks, type wiring),
"impl" (Protocol method -> the same method on each class implementing that Protocol).
Resolution follows names, imports, self.<method>, typed dataclass fields and properties, annotated
parameters, local `x = Class(...)`, `Class(...).method`, and subscripts of typed mappings. A call that is still
unresolved links only when its method name is unique in the graph (marked inferred).
Blind spots: dynamic dispatch, getattr, decorators that wrap, calls through untyped locals.
"""

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--package", action="append", default=[])
    parser.add_argument("--entry", action="append", default=[])
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def module_name(root: Path, path: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts).removesuffix(
        ".__init__"
    )


class Graph:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.nodes: dict[
            str, tuple[str, ast.AST, str | None, Path, bool]
        ] = {}  # id -> (module, node, owner, path, entry)
        self.trees: dict[str, ast.Module] = {}
        self.classes: dict[str, dict] = {}
        self.props: set[str] = set()
        self.edges: dict[tuple[str, str], dict] = {}
        self._imports: dict[str, dict[str, str]] = {}

    def add_file(self, path: Path, entry_filter: str | None, is_entry: bool) -> None:
        mod = module_name(self.root, path)
        tree = ast.parse(path.read_text())
        self.trees[mod] = tree
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_entry and entry_filter and entry_filter not in ast.unparse(node):
                    continue
                self.nodes[f"{mod}.{node.name}"] = (mod, node, None, path, is_entry)
            elif isinstance(node, ast.ClassDef) and not is_entry:
                self.add_class(mod, node, path)

    def add_class(self, mod: str, node: ast.ClassDef, path: Path) -> None:
        cq = f"{mod}.{node.name}"
        self.nodes[cq] = (mod, node, "class", path, False)
        fields = {}
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                fields[item.target.id] = ast.unparse(item.annotation)
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.nodes[f"{cq}.{item.name}"] = (mod, item, cq, path, False)
                is_property = any(
                    isinstance(d, ast.Name) and d.id in ("cached_property", "property")
                    for d in item.decorator_list
                )
                if is_property and item.returns is not None:
                    fields[item.name] = ast.unparse(item.returns)
                    self.props.add(f"{cq}.{item.name}")
        self.classes[cq] = {
            "fields": fields,
            "bases": [ast.unparse(b) for b in node.bases],
        }

    def imports(self, mod: str) -> dict[str, str]:
        if mod not in self._imports:
            names = {}
            for node in ast.walk(self.trees[mod]):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        names[alias.asname or alias.name] = (
                            f"{node.module}.{alias.name}"
                        )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        names[alias.asname or alias.name.split(".")[-1]] = alias.name
            self._imports[mod] = names
        return self._imports[mod]

    def resolve_name(self, name: str, mod: str) -> str | None:
        for candidate in (f"{mod}.{name}", self.imports(mod).get(name)):
            if candidate and candidate in self.nodes:
                return candidate
        return None

    def class_of(self, annotation: str, mod: str) -> str | None:
        name = annotation.split("[")[0].split("|")[0].strip().strip("'\"")
        found = self.resolve_name(name, mod)
        return found if found in self.classes else None

    def field_annotation(self, cq: str, name: str) -> tuple[str | None, str | None]:
        seen = set()
        while cq and cq not in seen:
            seen.add(cq)
            annotation = self.classes[cq]["fields"].get(name)
            if annotation:
                return annotation, cq.rsplit(".", 1)[0]
            mod = cq.rsplit(".", 1)[0]
            cq = next(
                (
                    b
                    for b in (
                        self.class_of(base, mod) for base in self.classes[cq]["bases"]
                    )
                    if b
                ),
                None,
            )
        return None, None

    def type_of(
        self,
        expr: ast.AST,
        owner: str | None,
        local_types: dict,
        value_of_mapping: bool = False,
    ) -> str | None:
        if isinstance(expr, ast.Name):
            return owner if expr.id == "self" and owner else local_types.get(expr.id)
        if isinstance(expr, ast.Attribute):
            base = self.type_of(expr.value, owner, local_types)
            if not base:
                return None
            annotation, mod = self.field_annotation(base, expr.attr)
            if not annotation:
                return None
            if value_of_mapping and "[" in annotation:
                annotation = (
                    annotation[annotation.find("[") + 1 : annotation.rfind("]")]
                    .split(",")[-1]
                    .strip()
                )
            return self.class_of(annotation, mod)
        if isinstance(expr, ast.Subscript):
            return self.type_of(expr.value, owner, local_types, value_of_mapping=True)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            return local_types.get(f"__call__{expr.func.id}")
        return None

    def method_of(self, cq: str | None, attr: str) -> str | None:
        seen = set()
        while cq and cq not in seen:
            seen.add(cq)
            if f"{cq}.{attr}" in self.nodes:
                return f"{cq}.{attr}"
            mod = cq.rsplit(".", 1)[0]
            cq = next(
                (
                    b
                    for b in (
                        self.class_of(base, mod) for base in self.classes[cq]["bases"]
                    )
                    if b
                ),
                None,
            )
        return None

    def build_edges(self) -> None:
        method_index = defaultdict(list)
        for q, (_, _, owner, _, _) in self.nodes.items():
            if owner and owner != "class":
                method_index[q.rsplit(".", 1)[1]].append(q)
        for q, (mod, fn, owner, _, _) in self.nodes.items():
            if owner == "class":
                continue
            calls = {id(c.func) for c in ast.walk(fn) if isinstance(c, ast.Call)}
            local_types = self.local_types(fn, mod)
            for node in ast.walk(fn):
                target, inferred = None, False
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    target = self.resolve_name(node.id, mod)
                elif isinstance(node, ast.Attribute):
                    target, inferred = self.resolve_attr(
                        node, mod, owner, local_types, id(node) in calls, method_index
                    )
                if target and target != q:
                    kind = "call" if id(node) in calls else "ref"
                    previous = self.edges.get((q, target))
                    if not previous or (previous["kind"] == "ref" and kind == "call"):
                        self.edges[(q, target)] = {
                            "from": q,
                            "to": target,
                            "kind": kind,
                            "inferred": inferred,
                        }
        self.add_protocol_edges()

    def local_types(self, fn: ast.AST, mod: str) -> dict:
        types = {}
        for node in ast.walk(fn):
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
            ):
                cq = self.class_of(node.value.func.id, mod)
                for target in node.targets:
                    if cq and isinstance(target, ast.Name):
                        types[target.id] = cq
            if isinstance(node, ast.arg) and node.annotation is not None:
                cq = self.class_of(ast.unparse(node.annotation), mod)
                if cq:
                    types[node.arg] = cq
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                cq = self.class_of(node.func.id, mod)
                if cq:
                    types[f"__call__{node.func.id}"] = cq
        return types

    def resolve_attr(
        self, node, mod, owner, local_types, is_call, method_index
    ) -> tuple[str | None, bool]:
        attr, base = node.attr, node.value
        found = self.method_of(self.type_of(base, owner, local_types), attr)
        if found:
            return found, False
        if isinstance(base, ast.Name):
            full = self.imports(mod).get(base.id)
            if full and f"{full}.{attr}" in self.nodes:
                return f"{full}.{attr}", False
            cq = self.resolve_name(base.id, mod)
            if cq in self.classes:
                found = self.method_of(cq, attr)
                if found:
                    return found, False
        if isinstance(base, ast.Attribute):
            # receiver type unknown (e.g. an IO object defined outside the graph): use the field's type when every
            # graphed class declaring a field of that name agrees on it
            types = {
                self.class_of(c["fields"][base.attr], cq.rsplit(".", 1)[0])
                for cq, c in self.classes.items()
                if base.attr in c["fields"]
            } - {None}
            if len(types) == 1:
                found = self.method_of(types.pop(), attr)
                if found:
                    return found, True
        candidates = method_index.get(attr, [])
        if (
            len(candidates) == 1
            and not attr.startswith("__")
            and (is_call or candidates[0] in self.props)
        ):
            return candidates[0], True
        return None, False

    def add_protocol_edges(self) -> None:
        protocols = [
            cq
            for cq, c in self.classes.items()
            if any(b.split("[")[0] == "Protocol" for b in c["bases"])
        ]
        for protocol in protocols:
            methods = {
                q.rsplit(".", 1)[1]
                for q, n in self.nodes.items()
                if n[2] == protocol and not q.rsplit(".", 1)[1].startswith("_")
            }
            if not methods:
                continue
            for cq in self.classes:
                if cq == protocol:
                    continue
                own = {m for m in methods if f"{cq}.{m}" in self.nodes}
                if len(own) / len(methods) >= 0.6:
                    for m in own:
                        key = (f"{protocol}.{m}", f"{cq}.{m}")
                        self.edges[key] = {
                            "from": key[0],
                            "to": key[1],
                            "kind": "impl",
                            "inferred": False,
                        }

    def to_json(self, prefix: str) -> dict:
        def short(q: str) -> str:
            return q.removeprefix(prefix + ".") if prefix else q

        nodes = []
        for q, (mod, node, owner, path, entry) in self.nodes.items():
            nodes.append(
                {
                    "id": short(q),
                    "module": short(mod) if short(mod) != mod or not prefix else mod,
                    "kind": "class"
                    if owner == "class"
                    else ("method" if owner else "function"),
                    "name": q.rsplit(".", 1)[1]
                    if owner in (None, "class")
                    else ".".join(q.split(".")[-2:]),
                    "path": str(path.relative_to(self.root)),
                    "line": node.lineno,
                    "loc": (node.end_lineno or node.lineno) - node.lineno + 1,
                    "doc": (ast.get_docstring(node) or "").strip().split("\n")[0],
                    "entry": entry,
                }
            )
        edges = [
            {**e, "from": short(e["from"]), "to": short(e["to"])}
            for e in self.edges.values()
        ]
        return {"nodes": nodes, "edges": edges}


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    graph = Graph(root)
    package_mods = []
    for package in args.package:
        directory = (root / package).resolve()
        package_mods.append(module_name(root, directory / "__init__.py"))
        for path in sorted(directory.rglob("*.py")):
            graph.add_file(path, None, is_entry=False)
    for entry in args.entry:
        file, _, needle = entry.partition("::")
        graph.add_file((root / file).resolve(), needle or None, is_entry=True)
    graph.build_edges()
    prefix = package_mods[0] if len(package_mods) == 1 else ""
    data = graph.to_json(prefix)
    args.out.write_text(json.dumps(data, separators=(",", ":")))
    counts = defaultdict(int)
    for edge in data["edges"]:
        counts[edge["kind"]] += 1
    inferred = sum(edge["inferred"] for edge in data["edges"])
    print(
        f"{len(data['nodes'])} symbols, {len(data['edges'])} edges {dict(counts)}, {inferred} inferred"
    )
    report_unreached(data)


def report_unreached(data: dict) -> None:
    """Functions and methods no entry point reaches: each is dead code or a call the resolver missed."""
    entries = [n["id"] for n in data["nodes"] if n["entry"]]
    if not entries:
        return
    outgoing = defaultdict(list)
    for edge in data["edges"]:
        outgoing[edge["from"]].append(edge["to"])
    reached, queue = set(entries), list(entries)
    while queue:
        for target in outgoing[queue.pop()]:
            if target not in reached:
                reached.add(target)
                queue.append(target)
    unreached = sorted(
        n["id"]
        for n in data["nodes"]
        if n["kind"] != "class" and n["id"] not in reached
    )
    print(
        f"{len(unreached)} functions/methods unreached from the {len(entries)} entry points:"
    )
    for symbol in unreached[:60]:
        print(f"  {symbol}")


if __name__ == "__main__":
    main()
