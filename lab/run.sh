#!/usr/bin/env bash
set -euo pipefail

help() {
    cat <<'EOF'
Usage: bash lab/run.sh [--dry] {1|2|3|4|all|transport|maxwell|mpi}
  1          Krylov methods and GMRES restart (laplacian)
  2          AMG growth and aggressive coarsening (laplacian)
  3, darcy   Mixed Darcy flow with two MGR policies
  4, file    thermal1 file comparison (hypredrive-cli)
  all        Required labs 1 through 4
Aliases: darcy=3, file=4, thermal1=4
  transport  Convection-diffusion (convdif)
  maxwell    Scalar AMG versus AMS (maxwell)
  mpi        Laplacian on 1, 2 and 4 MPI ranks
  --dry      Print commands only; no setup, solves or file writes
  -h, --help Show this help
Before setup, --dry uses executable names and /path/to/work.
EOF
}

dry=0
exercise=
for arg in "$@"; do
    case "$arg" in
        -h|--help) help; exit 0 ;;
        --dry) dry=1 ;;
        1|2|3|4|darcy|file|thermal1|all|transport|maxwell|mpi)
            [[ -z $exercise ]] || { help >&2; exit 2; }
            case "$arg" in
            3|darcy) exercise=darcy ;;
            4|file|thermal1) exercise=file ;;
            *)
                exercise=$arg ;;
            esac ;;
        *) help >&2; exit 2 ;;
    esac
done
[[ -n $exercise ]] || { help >&2; exit 2; }

LAB=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [[ $dry == 1 ]]; then
    WORK=/path/to/work
    bin=
    if [[ -f $LAB/.build-path ]]; then
        root=$(cat "$LAB/.build-path")
        WORK="$root/work"
        bin="$root/build/"
    fi
    LAP="${bin}laplacian" CLI="${bin}hypredrive-cli"
    DARCY="${bin}darcy"
    SPE10="$WORK/data/spe10_case2a/spe_perm.dat"
    CONVDIF="${bin}convdif" MAXWELL="${bin}maxwell"
else
    source "$LAB/activate.sh"
    cd "$WORK"
    mkdir -p out
fi

# One helper prints each copyable command, then runs it and retains its log.
logs=()
run() {
    local label=$1
    shift
    printf '(cd %q &&' "$WORK"
    printf ' %q' "$@"
    printf ')\n'
    [[ $dry == 0 ]] || return 0
    "$@" 2>&1 | tee "out/$label.txt"
    logs+=("out/$label.txt")
}

if [[ $exercise == 1 || $exercise == all ]]; then
    run krylov-n24-pcg-jacobi "$LAP" -ns 1 -n 24 24 24 -i "$LAB/configs/pcg-jacobi.yml" -v 1
    for n in 24 48; do
        for policy in pcg-fsai gmres-fsai bicgstab-fsai; do
            run "krylov-n$n-$policy" "$LAP" -ns 1 -n "$n" "$n" "$n" -i "$LAB/configs/$policy.yml" -v 1
        done
    done
    run krylov-n48-gmres-fsai-k5 "$LAP" -ns 1 -n 48 48 48 -i "$LAB/configs/gmres-fsai-k5.yml" -v 1
fi

if [[ $exercise == 2 || $exercise == all ]]; then
    for n in 24 48; do
        run "amg-n$n" "$LAP" -ns 1 -n "$n" "$n" "$n" -i "$LAB/configs/pcg-amg.yml" -v 1
    done
    for levels in 0 1 2; do
        run "amg-agg$levels" "$LAP" -ns 1 -n 48 48 48 -i "$LAB/configs/pcg-amg.yml" -v 1 -a \
            --preconditioner:amg:print_level 1 --preconditioner:amg:aggressive:num_levels "$levels"
    done
fi

if [[ $exercise == darcy || $exercise == all ]]; then
    [[ $dry == 1 || -s $SPE10 ]] || {
        echo "Missing SPE10 data. Run bash lab/setup.sh first." >&2; exit 1;
    }
    run darcy-mgr-default env OMPI_MCA_rmaps_base_oversubscribe=1 mpiexec -n 8 "$DARCY" \
        -n 30 110 85 -P 2 2 2 --K-file "$SPE10" \
        --K-file-grid 60 220 85 --K-file-k-order top-down -g y -v 1 \
        -i "$LAB/configs/darcy-mgr-default.yml"
    run darcy-mgr-strong env OMPI_MCA_rmaps_base_oversubscribe=1 mpiexec -n 8 "$DARCY" \
        -n 30 110 85 -P 2 2 2 --K-file "$SPE10" \
        --K-file-grid 60 220 85 --K-file-k-order top-down -g y -v 1 \
        -i "$LAB/configs/darcy-mgr-strong.yml"
fi

if [[ $exercise == file || $exercise == all ]]; then
    if [[ $dry == 0 && ! -f data/thermal1.mtx ]]; then
        python3 "$LAB/prepare.py" "$WORK"
    fi
    for policy in amg fsai ilu; do
        run "file-$policy" "$CLI" "$LAB/configs/file-$policy.yml"
    done
fi

case "$exercise" in
    transport)
        run transport-gmres "$CONVDIF" -n 32 8 8 -k 1e-4 -w 2 -nt 3 -i "$LAB/configs/gmres-amg.yml" -v 1 ;;
    maxwell)
        for policy in amg ams; do
            run "maxwell-$policy" "$MAXWELL" -ns 1 -n 12 12 12 -i "$LAB/configs/pcg-$policy.yml" -v 1
        done ;;
    mpi)
        for ranks in 1 2 4; do
            run "mpi-$ranks" mpiexec -n "$ranks" "$LAP" -ns 1 -n 48 48 48 -P "$ranks" 1 1 -i "$LAB/configs/pcg-amg.yml" -v 1
        done ;;
esac

if [[ $dry == 0 ]]; then
    python3 "$LAB/summarize.py" "${logs[@]}" --csv "out/summary-$exercise.csv"
    printf '\nRaw logs and summary: %s/out\n' "$WORK"
fi
