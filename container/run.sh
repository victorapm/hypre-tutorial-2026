#!/usr/bin/env bash
set -euo pipefail
help() {
    cat <<'EOF'
Usage: bash container/run.sh [--dry] {1|2|3|4|all|transport|maxwell|mpi|shell|info}
       bash container/run.sh suitesparse {list|fetch ID|run ID|run all}
Aliases: darcy=3, file=4
  --dry       Print the Docker command without starting a container or writing files.
  -h, --help  Show this help.
HYPRE_TUTORIAL_IMAGE selects a published image or a local image tag.
Results: results/container/; downloaded matrices: .cache/suitesparse/.
EOF
}
[[ $# -gt 0 ]] || { help; exit 0; }
dry=0
args=()
for arg in "$@"; do
    case "$arg" in
        -h|--help) help; exit 0 ;;
        --dry) dry=1 ;;
        *) args+=("$arg") ;;
    esac
done
[[ ${#args[@]} -gt 0 ]] || { help >&2; exit 2; }
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image=${HYPRE_TUTORIAL_IMAGE:-}
if [[ -z $image ]]; then
    origin=$(git -C "$repo" config --get remote.origin.url 2>/dev/null || true)
    case "$origin" in
        https://github.com/*) slug=${origin#https://github.com/} ;;
        git@github.com:*) slug=${origin#git@github.com:} ;;
        *) slug= ;;
    esac
    if [[ -n $slug ]]; then
        slug=$(printf '%s' "${slug%.git}" | tr '[:upper:]' '[:lower:]')
        image="ghcr.io/$slug:2026"
    else
        image=hypre-tutorial-2026:local
    fi
fi
results=${HYPRE_TUTORIAL_RESULTS:-$repo/results/container}
cache=${HYPRE_TUTORIAL_CACHE:-$repo/.cache/suitesparse}
[[ $results == /* && $cache == /* ]] || {
    echo 'HYPRE_TUTORIAL_RESULTS and HYPRE_TUTORIAL_CACHE must be absolute paths.' >&2; exit 2;
}
command=(docker run --rm --init --shm-size=256m)
if [[ -n ${HYPRE_TUTORIAL_PLATFORM:-} ]]; then
    command+=(--platform "$HYPRE_TUTORIAL_PLATFORM")
fi
if [[ -t 0 && -t 1 ]]; then command+=(-it); fi
command+=(--env "TUTORIAL_UID=$(id -u)" --env "TUTORIAL_GID=$(id -g)"
    --volume "$results:/opt/hypre-tutorial/work/out"
    --volume "$cache:/opt/hypre-tutorial/work/data/suitesparse"
    --volume "$repo/lab/configs:/tutorial/lab/configs:ro")
if [[ -n ${HYPRE_TUTORIAL_CA_BUNDLE:-} ]]; then
    [[ $HYPRE_TUTORIAL_CA_BUNDLE == /* && -r $HYPRE_TUTORIAL_CA_BUNDLE ]] || {
        echo 'HYPRE_TUTORIAL_CA_BUNDLE must be an absolute, readable PEM file.' >&2; exit 2;
    }
    command+=(--volume "$HYPRE_TUTORIAL_CA_BUNDLE:/run/tutorial-ca.pem:ro"
        --env SSL_CERT_FILE=/run/tutorial-ca.pem --env CURL_CA_BUNDLE=/run/tutorial-ca.pem)
fi
command+=("$image" "${args[@]}")
if [[ $dry == 1 ]]; then
    printf '%q ' "${command[@]}"; printf '\n'; exit 0
fi
docker info >/dev/null
if [[ $image == hypre-tutorial-2026:local ]] && ! docker image inspect "$image" >/dev/null 2>&1; then
    echo 'Set HYPRE_TUTORIAL_IMAGE to the published image, or build hypre-tutorial-2026:local first. See container/README.md.' >&2
    exit 1
fi
mkdir -p "$results" "$cache"
exec "${command[@]}"
