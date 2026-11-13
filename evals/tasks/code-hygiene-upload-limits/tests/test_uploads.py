import ast
import importlib
import io
import re
import sys
import tokenize
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app/app")
MB = 1024 * 1024
LIMIT_NUMBERS = {25, 25 * MB, 25_000_000}
LIMIT_IN_TEXT = re.compile(r"(?<![\d.])25(?![\d])")
STRING_TOKENS = {tokenize.STRING} | {getattr(tokenize, n) for n in ("FSTRING_MIDDLE",) if hasattr(tokenize, n)}


def _python_files():
    return [p for p in APP.rglob("*.py") if "__pycache__" not in p.parts]


@pytest.fixture(scope="module")
def service():
    return importlib.import_module("app.documents.service")


@pytest.fixture(scope="module")
def rejected():
    return importlib.import_module("app.documents.errors").UploadRejected


def test_rejects_file_over_limit_and_says_so(service, rejected):
    with pytest.raises(rejected) as info:
        service.upload_document("big.pdf", "application/pdf", b"\0" * (26 * MB))
    assert LIMIT_IN_TEXT.search(str(info.value)), f"message does not state the limit: {info.value}"


def test_accepts_previewable_file_within_limit(service):
    assert service.upload_document("ok.pdf", "application/pdf", b"\0" * (24 * MB)).size_bytes == 24 * MB
    service.upload_document("ok.png", "image/png", b"\x89PNG")


def test_rejects_unpreviewable_type(service, rejected):
    for content_type in ("text/plain", "image/gif"):
        with pytest.raises(rejected):
            service.upload_document("x", content_type, b"abc")


def _limit_occurrences():
    hits = []
    for path in _python_files():
        for tok in tokenize.generate_tokens(io.StringIO(path.read_text()).readline):
            if tok.type == tokenize.NUMBER:
                try:
                    value = int(tok.string.replace("_", ""))
                except ValueError:
                    continue
                if value in LIMIT_NUMBERS:
                    hits.append((path, tok.start[0], tok.string, tok.type))
            elif tok.type in STRING_TOKENS and LIMIT_IN_TEXT.search(tok.string):
                hits.append((path, tok.start[0], tok.string, tok.type))
    return hits


def test_size_limit_written_once_and_reused_in_message():
    hits = _limit_occurrences()
    assert len(hits) == 1, f"the 25 MB limit should be written once and referenced everywhere: {hits}"


def test_size_limit_constant_declared_at_top_of_module():
    hits = [h for h in _limit_occurrences() if h[3] == tokenize.NUMBER]
    assert hits, "no numeric size limit found"
    for path, line, _, _ in hits:
        body = ast.parse(path.read_text()).body
        first_def = next((n.lineno for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                                     ast.ClassDef))), float("inf"))
        owner = next((n for n in body if n.lineno <= line <= n.end_lineno), None)
        assert isinstance(owner, (ast.Assign, ast.AnnAssign)), f"{path}:{line} limit not a module-level constant"
        targets = owner.targets if isinstance(owner, ast.Assign) else [owner.target]
        assert all(isinstance(t, ast.Name) and re.fullmatch(r"[A-Z][A-Z0-9_]*", t.id) for t in targets), \
            f"{path}:{line} limit constant not UPPER_SNAKE"
        assert owner.lineno < first_def, f"{path}:{line} constant declared below a def/class"


def test_allowed_types_have_one_definition():
    counts = {}
    for path in _python_files():
        for tok in tokenize.generate_tokens(io.StringIO(path.read_text()).readline):
            if tok.type in STRING_TOKENS:
                for mime in ("application/pdf", "image/png", "image/jpeg"):
                    if mime in tok.string:
                        counts.setdefault(mime, []).append(f"{path.name}:{tok.start[0]}")
    duplicated = {m: locs for m, locs in counts.items() if len(locs) > 1}
    assert not duplicated, f"previewable types copied instead of imported: {duplicated}"
