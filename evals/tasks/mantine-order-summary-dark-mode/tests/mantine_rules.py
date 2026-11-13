"""Shared helpers: run the TSX linter, parse CSS modules, run the vitest verifier suite."""

import json
import re
import shutil
import subprocess
from pathlib import Path

APP = Path("/app")
SRC = APP / "src"

# CSS properties that a Mantine style prop (w, p, bg, bd, bdrs, ...) or a layout component
# (Stack/Group gap, justify, align, wrap) already expresses.
PROP_EXPRESSIBLE = {
    "width", "min-width", "max-width", "height", "min-height", "max-height",
    "background", "background-color", "background-size", "background-position",
    "background-repeat", "background-attachment", "color", "border", "border-radius", "opacity",
    "font-family", "font-size", "font-weight", "letter-spacing", "line-height", "font-style",
    "text-transform", "text-decoration", "text-align", "position", "top", "left", "bottom",
    "right", "inset", "display", "flex",
    "flex-direction", "gap", "row-gap", "column-gap", "justify-content", "align-items", "flex-wrap",
}
PROP_EXPRESSIBLE_PREFIXES = ("margin", "padding")
FRACTIONAL_LENGTH = re.compile(r"(?<![\w.])\d*\.\d+(rem|em|px|vh|vw)\b")
FRACTIONAL_NUMBER = re.compile(r"(?<![\w.])\d*\.\d+(?![\w%])")
HARDCODED_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(rgba?|hsla?)\(")


def lint_tsx():
    run = subprocess.run(
        ["node", "/tests/mantine_lint.cjs", str(SRC)], capture_output=True, text=True, timeout=120
    )
    assert run.returncode == 0, run.stderr[-3000:]
    return json.loads(run.stdout)


def findings(report, key):
    return [hit for per_file in report.values() for hit in per_file[key]]


def css_files():
    return sorted(p for p in SRC.rglob("*.css") if "node_modules" not in p.parts)


def _strip_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def css_rules(path):
    """Yield (selector, [(property, value)], at_rule_context) for every style rule."""
    text = _strip_comments(path.read_text())
    rules = []

    def parse(block, context):
        i = 0
        while i < len(block):
            open_at = block.find("{", i)
            if open_at == -1:
                return
            prelude = block[i:open_at].strip().split(";")[-1].strip()
            depth, j = 1, open_at + 1
            while j < len(block) and depth:
                depth += {"{": 1, "}": -1}.get(block[j], 0)
                j += 1
            body = block[open_at + 1 : j - 1]
            if prelude.startswith("@"):
                if not prelude.startswith("@keyframes"):
                    parse(body, context + [prelude])
            else:
                declarations = []
                for decl in body.split(";"):
                    if ":" in decl and "{" not in decl:
                        prop, value = decl.split(":", 1)
                        declarations.append((prop.strip().lower(), value.strip()))
                rules.append((prelude, declarations, context))
            i = j

    parse(text, [])
    return rules


def is_prop_expressible(prop):
    return prop in PROP_EXPRESSIBLE or prop.startswith(PROP_EXPRESSIBLE_PREFIXES)


def is_plain_class_selector(selector):
    return all(re.fullmatch(r"\.[\w-]+", part.strip()) for part in selector.split(","))


def run_vitest_verifier(test_file):
    verifier_dir = SRC / "__verifier__"
    report = Path("/tmp/vitest-verifier.json")
    verifier_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(test_file, verifier_dir / Path(test_file).name)
    report.unlink(missing_ok=True)
    run = subprocess.run(
        ["npx", "vitest", "run", "src/__verifier__", "--reporter=json", f"--outputFile={report}"],
        cwd=APP, capture_output=True, text=True, timeout=300,
    )
    shutil.rmtree(verifier_dir, ignore_errors=True)
    assert report.exists(), run.stdout[-3000:] + run.stderr[-3000:]
    data = json.loads(report.read_text())
    outcome = {}
    for file in data["testResults"]:
        if not file["assertionResults"]:
            outcome["__file__"] = ("failed", [file.get("message", "")])
        for case in file["assertionResults"]:
            outcome[case["title"]] = (case["status"], case.get("failureMessages", []))
    return outcome


def check_vitest(results, title):
    status, messages = results.get(title) or results.get("__file__", ("missing", []))
    assert status == "passed", f"{title}: {status}\n" + "\n".join(messages)[:3000]


def run_project_checks():
    for cmd in (["npm", "test", "--silent"], ["npx", "tsc", "--noEmit"]):
        run = subprocess.run(cmd, cwd=APP, capture_output=True, text=True, timeout=300)
        assert run.returncode == 0, f"{' '.join(cmd)}\n{run.stdout[-3000:]}{run.stderr[-3000:]}"


# --- rule checks shared by every mantine task -------------------------------------------------


def assert_no_inline_style(report):
    hits = findings(report, "inlineStyle")
    assert not hits, f"inline style= props (use a style prop, or a CSS module class when none exists): {hits}"


def assert_no_prop_only_css_class():
    offenders = []
    for path in css_files():
        for selector, declarations, context in css_rules(path):
            if context or not declarations or not is_plain_class_selector(selector):
                continue
            if all(is_prop_expressible(prop) for prop, _ in declarations):
                offenders.append(f"{path.relative_to(APP)} {selector} {{{'; '.join(p for p, _ in declarations)}}}")
    assert not offenders, f"CSS classes that only set what Mantine props/layout components express: {offenders}"


def assert_no_hand_rolled_flex(report):
    offenders = list(findings(report, "handRolledFlex"))
    for path in css_files():
        for selector, declarations, _ in css_rules(path):
            for prop, value in declarations:
                if prop == "display" and value.split()[0] in ("flex", "inline-flex"):
                    offenders.append(f"{path.relative_to(APP)} {selector}")
    assert not offenders, f"hand-rolled flex layout instead of Stack/Group: {offenders}"


def assert_no_braced_string_literals(report):
    hits = findings(report, "bracedStringLiteral")
    assert not hits, f"string literal wrapped in braces (write w=\"100%\", not w={{\"100%\"}}): {hits}"


def assert_no_fractional_values(report):
    offenders = list(findings(report, "fractionalValue"))
    for path in css_files():
        for selector, declarations, _ in css_rules(path):
            for prop, value in declarations:
                if FRACTIONAL_LENGTH.search(value) or (prop == "line-height" and FRACTIONAL_NUMBER.search(value)):
                    offenders.append(f"{path.relative_to(APP)} {selector} {prop}: {value}")
    assert not offenders, f"fractional sizes/line-heights (use a theme token or whole px/rem): {offenders}"


def assert_no_hardcoded_colors(report):
    offenders = list(findings(report, "hardcodedColor"))
    for path in css_files():
        for selector, declarations, _ in css_rules(path):
            for prop, value in declarations:
                if HARDCODED_COLOR.search(value):
                    offenders.append(f"{path.relative_to(APP)} {selector} {prop}: {value}")
    assert not offenders, f"hardcoded colours (use theme tokens / --mantine-color-* vars): {offenders}"
