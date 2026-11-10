"""Expand the curated matrix input into a temporary lab workspace."""
import gzip
import hashlib
import shutil
import sys
from pathlib import Path

lab = Path(__file__).resolve().parent
archive = lab / "data/thermal1.mtx.gz"
expected = (lab / "data/thermal1.mtx.gz.sha256").read_text().split()[0]
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit("Matrix checksum mismatch. Restore lab/data/thermal1.mtx.gz.")
work = Path(sys.argv[1])
(work / "data").mkdir(parents=True, exist_ok=True)
with gzip.open(archive, "rb") as src, (work / "data/thermal1.mtx").open("wb") as dst:
    shutil.copyfileobj(src, dst)
print(f"Prepared {work / 'data/thermal1.mtx'}")
