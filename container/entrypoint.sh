#!/usr/bin/env bash
set -euo pipefail
student_uid=${TUTORIAL_UID:-1000}
student_gid=${TUTORIAL_GID:-1000}
[[ $student_uid =~ ^[0-9]+$ && $student_gid =~ ^[0-9]+$ ]] || {
    echo 'TUTORIAL_UID and TUTORIAL_GID must be numeric.' >&2; exit 2;
}
# Give MPI a real passwd entry, including when the host UID differs from 1000.
if ! getent passwd "$student_uid" >/dev/null; then
    getent group "$student_gid" >/dev/null || groupadd --gid "$student_gid" tutorial
    useradd --uid "$student_uid" --gid "$student_gid" --no-create-home \
        --home-dir /tmp --shell /bin/bash tutorial
fi
source /tutorial/lab/activate.sh
if [[ $student_uid == 0 ]]; then
    export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
fi
mkdir -p "$WORK/out" "$WORK/data/suitesparse"
# Change only the mount roots, leaving previously saved files untouched.
chown "$student_uid:$student_gid" "$WORK/out" "$WORK/data/suitesparse"
case "${1:---help}" in
    shell)
        shift
        exec gosu "$student_uid:$student_gid" bash --noprofile --norc "$@" ;;
    suitesparse)
        shift
        exec gosu "$student_uid:$student_gid" python3 "$LAB/suitesparse.py" "$@" ;;
    info)
        exec gosu "$student_uid:$student_gid" cat "$HYPRE_TUTORIAL_BUILD_INFO" ;;
    *)
        exec gosu "$student_uid:$student_gid" bash "$LAB/run.sh" "$@" ;;
esac
