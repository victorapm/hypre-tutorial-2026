# Source this file from Bash or Zsh. It does not change the working directory.
if [[ -n ${BASH_VERSION:-} ]]; then
    _stanford_lab=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
elif [[ -n ${ZSH_VERSION:-} ]]; then
    _stanford_lab=$(cd "$(dirname "${(%):-%N}")" && pwd)
else
    echo 'Use Bash or Zsh to source lab/activate.sh.' >&2
    return 1
fi
if [[ ! -f $_stanford_lab/.build-path ]]; then
    echo 'Run bash lab/setup.sh first.' >&2
    return 1
fi
_stanford_root=$(cat "$_stanford_lab/.build-path")
if [[ ! -x $_stanford_root/build/hypredrive-cli ]]; then
    echo 'Build no longer exists under /tmp. Run setup again.' >&2
    return 1
fi
_stanford_xtrace_was_enabled=0
case "$-" in *x*) _stanford_xtrace_was_enabled=1 ;; esac
if [[ $_stanford_xtrace_was_enabled == 0 ]]; then
    set -x
fi
export LAB="$_stanford_lab" WORK="$_stanford_root/work"
export SPE10="$_stanford_root/work/data/spe10_case2a/spe_perm.dat"
export CLI="$_stanford_root/build/hypredrive-cli"
export LAP="$_stanford_root/build/laplacian"
export DARCY="$_stanford_root/build/darcy"
export CONVDIF="$_stanford_root/build/convdif"
export MAXWELL="$_stanford_root/build/maxwell"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
unset _stanford_lab _stanford_root
if [[ $_stanford_xtrace_was_enabled == 0 ]]; then
    set +x
fi
unset _stanford_xtrace_was_enabled
