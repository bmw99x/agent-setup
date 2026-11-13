import ast
import importlib
import logging
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, "/app")

APP_DIR = Path("/app/app")
JOB_SOURCE = Path("/app/app/settlements/job.py")
CATCH_ALL_TYPES = {"Exception", "BaseException"}
LOCAL_LOGGING_SETUP = {"getLogger", "basicConfig", "StreamHandler", "FileHandler", "Formatter", "addHandler", "dictConfig"}


class FakeDownload:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def readall(self) -> bytes:
        return self.payload

    def content_as_bytes(self, *args, **kwargs) -> bytes:
        return self.payload

    def content_as_text(self, encoding: str = "UTF-8", *args, **kwargs) -> str:
        return self.payload.decode(encoding)

    def chunks(self):
        yield self.payload

    def readinto(self, stream) -> int:
        stream.write(self.payload)
        return len(self.payload)


class FakeBlobClient:
    def __init__(self, container: "FakeContainer", name: str) -> None:
        self.container = container
        self.blob_name = name

    def download_blob(self, *args, **kwargs) -> FakeDownload:
        return self.container.download_blob(self.blob_name)


class FakeContainer:
    """Duck-types the parts of azure.storage.blob.ContainerClient a job would use."""

    container_name = "settlements"

    def __init__(self, blobs: dict[str, bytes | BaseException]) -> None:
        self.blobs = blobs

    def blob_properties(self, name_starts_with=None):
        return [
            SimpleNamespace(name=name, container="settlements", size=0)
            for name in self.blobs
            if name_starts_with is None or name.startswith(name_starts_with)
        ]

    def list_blobs(self, name_starts_with=None, *args, **kwargs):
        return iter(self.blob_properties(name_starts_with))

    def walk_blobs(self, name_starts_with=None, *args, **kwargs):
        return iter(self.blob_properties(name_starts_with))

    def list_blob_names(self, *args, name_starts_with=None, **kwargs):
        return iter(blob.name for blob in self.blob_properties(name_starts_with))

    def get_blob_client(self, blob, *args, **kwargs) -> FakeBlobClient:
        return FakeBlobClient(self, getattr(blob, "name", blob))

    def download_blob(self, blob, *args, **kwargs) -> FakeDownload:
        content = self.blobs[getattr(blob, "name", blob)]
        if isinstance(content, BaseException):
            raise content
        return FakeDownload(content)


@pytest.fixture(scope="module")
def job():
    return importlib.import_module("app.settlements.job")


def totals_of(job, blobs) -> dict[str, Decimal]:
    result = job.total_settlements(FakeContainer(blobs))
    return {merchant: Decimal(str(total)) for merchant, total in dict(result).items()}


def source_tree() -> ast.Module:
    return ast.parse(JOB_SOURCE.read_text())


def test_totals_valid_csv_blobs_and_ignores_other_files(job):
    blobs = {
        "2026-11-11/a.csv": b"merchant_id,amount\nm-1,10.50\nm-2,3.25\n",
        "2026-11-11/b.csv": b"merchant_id,amount\nm-1,4.50\n",
        "2026-11-11/README.txt": b"not a csv",
    }
    assert totals_of(job, blobs) == {"m-1": Decimal("15.00"), "m-2": Decimal("3.25")}


def test_malformed_file_is_skipped_whole_and_logged(job, caplog):
    blobs = {
        "good.csv": b"merchant_id,amount\nm-1,10.00\n",
        "bad-amount.csv": b"merchant_id,amount\nm-1,5.00\nm-2,twelve\n",
        "bad-columns.csv": b"merchant,value\nm-1,7.00\n",
    }
    with caplog.at_level(logging.DEBUG):
        totals = totals_of(job, blobs)
    assert totals == {"m-1": Decimal("10.00")}
    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "bad-amount.csv" in logged and "bad-columns.csv" in logged


def test_unexpected_errors_propagate(job):
    blobs = {
        "good.csv": b"merchant_id,amount\nm-1,10.00\n",
        "outage.csv": RuntimeError("storage outage"),
    }
    with pytest.raises(RuntimeError, match="storage outage"):
        totals_of(job, blobs)


def test_no_catch_all_except_outside_a_reraising_boundary():
    offenders = []
    for node in ast.walk(source_tree()):
        if not isinstance(node, ast.ExceptHandler):
            continue
        caught = node.type
        names = []
        if caught is None:
            names = ["<bare>"]
        else:
            elements = caught.elts if isinstance(caught, ast.Tuple) else [caught]
            names = [ast.unparse(element).rsplit(".", 1)[-1] for element in elements]
        is_catch_all = "<bare>" in names or CATCH_ALL_TYPES & set(names)
        reraises = any(isinstance(inner, ast.Raise) for inner in ast.walk(node))
        if is_catch_all and not reraises:
            offenders.append(f"line {node.lineno}: except {', '.join(names)}")
    assert not offenders, offenders


def test_credential_chain_is_named_not_default():
    referenced = {
        node.id if isinstance(node, ast.Name) else node.attr
        for node in ast.walk(source_tree())
        if isinstance(node, (ast.Name, ast.Attribute))
    }
    imported = {
        alias.asname or alias.name
        for node in ast.walk(source_tree())
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    names = referenced | imported
    assert "DefaultAzureCredential" not in names
    assert {"ManagedIdentityCredential", "AzureCliCredential"} <= names


def test_no_default_credential_anywhere_in_app():
    offenders = [str(path) for path in APP_DIR.rglob("*.py") if "DefaultAzureCredential" in path.read_text()]
    assert not offenders, offenders


def test_logger_comes_from_the_app_logging_module():
    offenders = []
    for node in ast.walk(source_tree()):
        if isinstance(node, ast.Call):
            called = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if called in LOCAL_LOGGING_SETUP:
                offenders.append(f"line {node.lineno}: {ast.unparse(node.func)}")
    assert not offenders, offenders
