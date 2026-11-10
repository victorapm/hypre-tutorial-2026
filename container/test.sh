#!/usr/bin/env bash
set -euo pipefail
image=${1:-hypre-tutorial-2026:local}
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$repo/results"
results=${2:-$(mktemp -d "$repo/results/container-test-XXXXXXXX")}
mkdir -p "$results"
export HYPRE_TUTORIAL_IMAGE="$image" HYPRE_TUTORIAL_RESULTS="$results"
export HYPRE_TUTORIAL_CACHE="$results/matrix-cache"
export HYPRE_TUTORIAL_PLATFORM=$(docker image inspect "$image" --format '{{.Os}}/{{.Architecture}}')
bash "$repo/container/run.sh" info > "$results/environment.json"
python3 - "$repo/lab/versions.env" "$results/environment.json" <<'PY'
from pathlib import Path
import json
import sys
pins = dict(line.split("=", 1) for line in Path(sys.argv[1]).read_text().splitlines()
            if line and not line.startswith("#"))
info = json.loads(Path(sys.argv[2]).read_text())
if (info["hypredrive_revision"] != pins["HYPREDRIVE_REV"] or
        info.get("hypredrive_version") != pins["HYPREDRIVE_VERSION"] or
        info.get("hypre_version") != pins["HYPRE_REV"]):
    raise SystemExit("Container solver versions/revision differ from the tutorial pins.")
PY
bash "$repo/container/run.sh" --dry 4 > "$results/docker-command.txt"
bash "$repo/container/run.sh" --dry 3 > "$results/docker-darcy-command.txt"
bash "$repo/container/run.sh" all > "$results/all.log" 2>&1
bash "$repo/container/run.sh" mpi > "$results/mpi.log" 2>&1
bash "$repo/container/run.sh" shell -c \
    'cd "$WORK" && mpiexec -n 2 "$CLI" "$LAB/configs/file-amg.yml"' \
    > "$results/mtx-mpi.txt" 2>&1
python3 - "$results/mtx-mpi.txt" <<'PY'
from pathlib import Path
import re
import sys
text = Path(sys.argv[1]).read_text()
if "with 82654 rows and 574458 nonzeros" not in text:
    raise SystemExit("Two-rank MTX solve loaded the wrong matrix dimensions/entry count.")
if re.search(r"Abort\(|MPI_Finalize failed|Fatal error", text):
    raise SystemExit("Two-rank MTX solve reported an MPI failure.")
PY
python3 "$repo/lab/compare.py" "$results" > "$results/comparison.txt"
python3 "$repo/lab/summarize.py" "$results"/krylov-*.txt "$results"/amg-*.txt \
    "$results"/file-*.txt "$results"/darcy-*.txt "$results"/mpi-*.txt "$results/mtx-mpi.txt" \
    --csv "$results/summary.csv"
printf '\nContainer labs, Darcy/MGR, 1/2/4-rank MPI, and parallel MTX passed. Evidence: %s\n' "$results"
