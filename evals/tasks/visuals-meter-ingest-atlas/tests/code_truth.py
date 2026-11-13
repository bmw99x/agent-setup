"""Ground truth from the repo's own source: every symbol, and who calls whom, resolved with ast.

Resolution covers what this repo uses: imported names and modules, `self.<field>` typed by a class
annotation, locals bound to `Class(...)`, `Class(...).method`, references passed as values (partial), and
Protocol methods dispatching to each class that implements them. `getattr` with a runtime name is not
resolved; tests treat it separately.
"""

import ast
import subprocess
from pathlib import PurePosixPath


class Code:
    def __init__(self, sources: dict[str, str]) -> None:
        self.modules: dict[str, ast.Module] = {}
        self.functions: dict[str, ast.AST] = {}  # "mod.func" / "mod.Class.method"
        self.classes: dict[str, ast.ClassDef] = {}
        for path, text in sorted(sources.items()):
            mod = ".".join(PurePosixPath(path).with_suffix("").parts).removesuffix(".__init__")
            tree = ast.parse(text)
            self.modules[mod] = tree
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.functions[f"{mod}.{node.name}"] = node
                elif isinstance(node, ast.ClassDef):
                    self.classes[f"{mod}.{node.name}"] = node
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            self.functions[f"{mod}.{node.name}.{item.name}"] = item

    @staticmethod
    def key(qualified: str) -> str:
        parts = qualified.split(".")
        return ".".join(parts[-2:]) if parts[-2][:1].isupper() else parts[-1]

    def symbol_keys(self) -> set[str]:
        return {self.key(q) for q in self.functions} | {q.split(".")[-1] for q in self.classes}

    def imports(self, mod: str) -> dict[str, str]:
        names = {}
        for node in ast.walk(self.modules[mod]):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    names[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        return names

    def resolve(self, name: str, mod: str) -> str | None:
        for candidate in (f"{mod}.{name}", self.imports(mod).get(name)):
            if candidate and (candidate in self.functions or candidate in self.classes or candidate in self.modules):
                return candidate
        return None

    def field_class(self, cls: str, field: str) -> str | None:
        mod = cls.rsplit(".", 1)[0]
        for item in self.classes[cls].body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == field:
                found = self.resolve(ast.unparse(item.annotation).split("[")[0], mod)
                return found if found in self.classes else None
        return None

    def is_protocol(self, cls: str) -> bool:
        return any(ast.unparse(b).split("[")[0] == "Protocol" for b in self.classes[cls].bases)

    def implementers(self, protocol: str, method: str) -> list[str]:
        wanted = {f.split(".")[-1] for f in self.functions if f.rsplit(".", 1)[0] == protocol}
        found = []
        for cls in self.classes:
            own = {f.split(".")[-1] for f in self.functions if f.rsplit(".", 1)[0] == cls}
            if cls != protocol and wanted <= own:
                found.append(f"{cls}.{method}")
        return found

    def type_of(self, expr: ast.AST, mod: str, owner: str | None, local: dict[str, str]) -> str | None:
        if isinstance(expr, ast.Name):
            if expr.id == "self":
                return owner
            if expr.id in local:
                return local[expr.id]
            found = self.resolve(expr.id, mod)
            return found if found in self.classes or found in self.modules else None
        if isinstance(expr, ast.Attribute):
            base = self.type_of(expr.value, mod, owner, local)
            return self.field_class(base, expr.attr) if base in self.classes else None
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            found = self.resolve(expr.func.id, mod)
            return found if found in self.classes else None
        return None

    def callees(self, qualified: str) -> set[str]:
        fn = self.functions[qualified]
        mod = next(m for m in sorted(self.modules, key=len, reverse=True) if qualified.startswith(m + "."))
        owner = qualified.rsplit(".", 1)[0] if qualified.rsplit(".", 1)[0] in self.classes else None
        local = {}
        for arg in fn.args.args + fn.args.kwonlyargs:
            if arg.annotation is not None:
                found = self.resolve(ast.unparse(arg.annotation).split("[")[0], mod)
                if found in self.classes:
                    local[arg.arg] = found
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                cls = self.type_of(node.value, mod, owner, local)
                for target in node.targets:
                    if cls and isinstance(target, ast.Name):
                        local[target.id] = cls
        found = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in local:
                target = self.resolve(node.id, mod)
                if target in self.functions:
                    found.add(target)
            elif isinstance(node, ast.Attribute):
                base = self.type_of(node.value, mod, owner, local)
                if base and f"{base}.{node.attr}" in self.functions:
                    found.add(f"{base}.{node.attr}")
        return found - {qualified}

    def edges(self) -> set[tuple[str, str]]:
        pairs = {(q, callee) for q in self.functions for callee in self.callees(q)}
        for cls in self.classes:
            if self.is_protocol(cls):
                for q in [f for f in self.functions if f.rsplit(".", 1)[0] == cls]:
                    pairs |= {(q, impl) for impl in self.implementers(cls, q.split(".")[-1])}
        return pairs

    def transitive_callers(self, target: str) -> set[str]:
        incoming: dict[str, set[str]] = {}
        for source, callee in self.edges():
            incoming.setdefault(callee, set()).add(source)
        seen, queue = {target}, [target]
        while queue:
            for caller in incoming.get(queue.pop(), ()):
                if caller not in seen:
                    seen.add(caller)
                    queue.append(caller)
        return {self.key(q) for q in seen - {target}}


def load(repo: str = "/app", rev: str | None = None) -> Code:
    """The Python sources at the commit the task was built on (default: /etc/eval-base-sha), read from git
    objects so nothing the agent adds or edits in the working tree changes the truth."""
    rev = rev or open("/etc/eval-base-sha").read().strip()

    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout

    paths = [p for p in git("ls-tree", "-r", "--name-only", rev).splitlines() if p.endswith(".py")]
    return Code({p: git("show", f"{rev}:{p}") for p in paths})
