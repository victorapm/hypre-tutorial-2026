#!/usr/bin/env bash
set -euo pipefail
set -x
lab=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$lab/versions.env"
jobs=${JOBS:-4}
reuse=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --reuse) reuse=1; shift ;;
        --jobs) jobs=${2:?Missing job count}; shift 2 ;;
        *) echo 'Usage: bash lab/setup.sh [--reuse] [--jobs N]' >&2; exit 2 ;;
    esac
done
[[ $jobs =~ ^[1-9][0-9]*$ ]] || { echo 'Jobs must be a positive integer.' >&2; exit 2; }
for tool in git cmake mpicc mpiexec python3 curl unzip; do
    command -v "$tool" >/dev/null || { echo "Install $tool first. See lab/README.md." >&2; exit 1; }
done
if [[ $reuse == 1 ]]; then
    work_root=$(cat "$lab/.build-path")
    [[ $work_root == /tmp/stanford26-* && -d $work_root/source/.git ]] || {
        echo 'No existing Stanford build to reuse. Run setup without --reuse.' >&2; exit 1;
    }
    [[ $(git -C "$work_root/source" rev-parse HEAD) == "$HYPREDRIVE_REV" ]] || {
        echo 'Existing source revision differs from the lab pin.' >&2; exit 1;
    }
else
    platform=$(uname -s | tr '[:upper:]' '[:lower:]')
    work_root=$(mktemp -d "/tmp/stanford26-${platform}-cpu-release-XXXXXXXX")
    git clone --quiet --no-checkout https://github.com/hypre-space/hypredrive.git "$work_root/source"
    git -C "$work_root/source" checkout --quiet --detach "$HYPREDRIVE_REV"
fi
# Save the configuration as soon as source retrieval succeeds, so --reuse can
# resume a first build interrupted during configuration or compilation.
printf '%s\n' "$work_root" > "$lab/.build-path"
cmake -S "$work_root/source" -B "$work_root/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$work_root/install" \
    -DCMAKE_DISABLE_FIND_PACKAGE_HYPRE=ON -DHYPRE_VERSION="$HYPRE_REV" \
    -DHYPREDRV_ENABLE_EXAMPLES=ON -DHYPREDRV_ENABLE_EXAMPLE_OMP=OFF \
    -DHYPREDRV_ENABLE_TESTING=OFF -DHYPREDRV_ENABLE_DATA=OFF \
    -DHYPRE_ENABLE_OPENMP=OFF -DHYPRE_ENABLE_CUDA=OFF \
    -DHYPRE_ENABLE_HIP=OFF -DHYPRE_ENABLE_SYCL=OFF \
    -DHYPREDRV_ENABLE_CUDA=OFF -DHYPREDRV_ENABLE_HIP=OFF \
    -DHYPREDRV_ENABLE_SYCL=OFF 2>&1 | tee "$work_root/configure.log"
cmake --build "$work_root/build" --parallel "$jobs" \
    --target hypredrive-cli laplacian darcy convdif maxwell 2>&1 | tee "$work_root/build.log"
mkdir -p "$work_root/work/data" "$work_root/work/out"
python3 "$lab/prepare.py" "$work_root/work"
if [[ ! -s $work_root/work/data/spe10_case2a/spe_perm.dat ]]; then
    bash "$work_root/source/scripts/download_spe10_case2a.sh" \
        "$work_root/work/data/spe10_case2a"
fi
printf '\nReady. Run from the workshop repository root:\n  source lab/activate.sh\n  bash lab/run.sh 1\nBuilds and logs: %s\n' "$work_root"
