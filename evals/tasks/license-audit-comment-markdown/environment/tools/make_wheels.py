"""Build a pure-Python wheel from each package source dir: <dir>/METADATA plus its modules."""
import base64
import hashlib
import sys
import zipfile
from pathlib import Path


def _digest(data: bytes) -> str:
    return "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()


def build(src: Path, out: Path) -> Path:
    metadata = (src / "METADATA").read_text()
    fields = dict(line.split(": ", 1) for line in metadata.splitlines() if ": " in line)
    name, version = fields["Name"].replace("-", "_"), fields["Version"]
    dist_info = f"{name}-{version}.dist-info"
    entries = {p.relative_to(src).as_posix(): p.read_bytes()
               for p in sorted(src.rglob("*")) if p.is_file() and p.name != "METADATA"}
    entries[f"{dist_info}/METADATA"] = metadata.encode()
    entries[f"{dist_info}/WHEEL"] = b"Wheel-Version: 1.0\nGenerator: eval\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    record = "".join(f"{path},{_digest(data)},{len(data)}\n" for path, data in entries.items())
    record += f"{dist_info}/RECORD,,\n"
    wheel = out / f"{name}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as zf:
        for path, data in entries.items():
            zf.writestr(path, data)
        zf.writestr(f"{dist_info}/RECORD", record)
    return wheel


if __name__ == "__main__":
    source_root, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    for pkg in sorted(p for p in source_root.iterdir() if p.is_dir()):
        print(build(pkg, out_dir))
