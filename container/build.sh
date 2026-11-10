#!/usr/bin/env bash
set -euo pipefail
jobs=${1:-2}
prefix=/opt/hypre-tutorial
bash lab/setup.sh --jobs "$jobs"
root=$(cat lab/.build-path)
# The pinned Darcy example builds but has no upstream install rule.
darcy_cmake="$root/source/examples/src/C_darcy/CMakeLists.txt"
if ! grep -q 'install(TARGETS darcy' "$darcy_cmake"; then
    cat >> "$darcy_cmake" <<'CMAKE'

# Install the Darcy mini-app into the container image.
install(TARGETS darcy RUNTIME DESTINATION bin)
CMAKE
fi
cmake -S "$root/source" -B "$root/build"
# Build remaining configured targets so the upstream installation is complete.
cmake --build "$root/build" --parallel "$jobs"
cmake --install "$root/build" --prefix "$prefix"
ln -s bin "$prefix/build"
mkdir -p "$prefix/work/data/suitesparse" "$prefix/work/out" "$prefix/share/licenses/hypre"
cp "$root/work/data/thermal1.mtx" "$prefix/work/data/thermal1.mtx"
mkdir -p "$prefix/work/data/spe10_case2a"
cp "$root/work/data/spe10_case2a/spe_perm.dat" "$prefix/work/data/spe10_case2a/spe_perm.dat"
cp "$root/build/_deps/hypre-src/"{COPYRIGHT,LICENSE-MIT,LICENSE-APACHE} "$prefix/share/licenses/hypre/"
python3 - "$root" "$prefix" <<'PY'
from pathlib import Path
import json
import os
import platform
import subprocess
import sys
root, prefix = map(Path, sys.argv[1:])
def output(command):
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
pins = dict(line.split("=", 1) for line in Path("lab/versions.env").read_text().splitlines()
            if line and not line.startswith("#"))
info = {
    "platform": platform.platform(), "architecture": platform.machine(),
    "hypredrive_version": pins["HYPREDRIVE_VERSION"],
    "hypre_version": pins["HYPRE_REV"],
    "hypredrive_revision": output(["git", "-C", str(root / "source"), "rev-parse", "HEAD"]),
    "hypre_revision": output(["git", "-C", str(root / "build/_deps/hypre-src"), "rev-parse", "HEAD"]),
    "compiler": output([os.environ.get("CC", "cc"), "--version"]), "mpi": output(["mpiexec", "--version"]),
    "cmake": output(["cmake", "--version"]), "python": platform.python_version(),
    "build": "Release; OpenMP, CUDA, HIP and SYCL disabled",
    "runtime": "CPU, one thread per rank; Lab 3 uses 8 ranks on a 2x2x2 grid; optional MPI uses 1/2/4 ranks",
}
(prefix / "build-info.json").write_text(json.dumps(info, indent=2) + "\n")
PY
