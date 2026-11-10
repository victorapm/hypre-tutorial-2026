# Local hands-on exercises

Run commands from the **workshop repository root**, which contains `lab/`.
Audience assumption: you know sparse matrices and basic PDE discretization;
no hypre API experience is required. The required path uses the CPU, one MPI
rank and one thread per rank. Labs 1, 2 and 4 use one MPI rank; Lab 3 uses
eight ranks on a 2x2x2 grid. The four labs take 10, 10, 5 and 15 minutes.

Expand the questions in [ANSWERS.md](ANSWERS.md) for reference responses.
The tutorial pins hypredrive **v0.4.0** and hypre **v3.2.1**.

## Before class

Install a native C/C++ compiler, Git, CMake 3.23 or newer, MPI, and Python 3.
The scripts use Bash. Setup needs internet access to fetch the pinned source
and SPE10 permeability input. After setup, required exercises use local data.

**macOS, including Apple Silicon:** install Xcode Command Line Tools and
Homebrew if not already available. Then:

```bash
xcode-select --install  # skip if the tools are already installed
brew install cmake python
brew install open-mpi   # skip if a working MPI installation is already available
```

Use a native Terminal on Apple Silicon and keep the compiler, MPI and CMake
on the same architecture. The lab disables OpenMP so Apple's Clang does not
need a separate OpenMP runtime. It uses host execution throughout.
Apple's Bash 3.2 and Zsh activation were validated on an M5 Max with Homebrew
MPICH 5.0.2; Open MPI is another supported MPI choice. Keep `mpicc` and
`mpiexec` from the same installation. macOS supplies `curl` and `unzip`.

**Ubuntu / Debian Linux, or Ubuntu under Windows WSL2:**

```bash
sudo apt-get update
sudo apt-get install build-essential cmake git curl unzip openmpi-bin libopenmpi-dev python3
```

Windows attendees should use WSL2 for these Bash instructions. Native Windows
builds use a different toolchain and are outside this workshop's setup path.

Then, on any supported setup:

```bash
bash lab/setup.sh --jobs 4
source lab/activate.sh
"$LAP" -ns 1 -n 12 12 12 -i "$LAB/configs/pcg-amg.yml" -v 1
```

Setup traces the commands it runs, including CMake; sourcing activate.sh
prints the commands that export the lab paths and executables.

The last command should print one statistics row with relative residual below
`1e-8`. Do this before class. Compilation time is outside the 90-minute slot.
On the presenter's 18-core M5, `--jobs 8` or `--jobs 12` is an optional build
choice. More build jobs do not change runtime MPI ranks.

Setup creates a unique `/tmp/stanford26-*-cpu-release-*` directory containing
the pinned source, out-of-source Release build, extracted matrices, and logs.
It downloads SPE10 Model 2 case 2a with the helper in the pinned hypredrive
source; the permeability input remains in the temporary workspace. Its path is
saved in the ignored `lab/.build-path`. To resume an interrupted build, use
`bash lab/setup.sh --reuse`. If the temporary directory has been cleaned by
the operating system, rerun setup without `--reuse`.

`source lab/activate.sh` works in Bash or Zsh and defines:

| Variable | Meaning |
|---|---|
| `LAB` | Absolute path of this lab folder |
| `WORK` | Temporary workspace, including `data/` and `out/` |
| `LAP` | Laplacian mini-app executable |
| `DARCY` | Mixed Darcy mini-app executable |
| `SPE10` | SPE10 case 2a permeability input |
| `CLI` | `hypredrive-cli` executable for file input |
| `CONVDIF`, `MAXWELL` | Optional mini-app executables |

The required mini-app commands launch as MPI singletons. Optional multi-rank
runs use `mpiexec` from the same MPI installation as `mpicc`.

Preview the commands or show the exercise list:

```bash
bash lab/run.sh --help
bash lab/run.sh --dry 3     # two Darcy/MGR commands
bash lab/run.sh --dry 4     # three hypredrive-cli commands for thermal1
bash lab/run.sh 1 --dry     # expanded Laplacian commands for Lab 1
```

`--dry` prints copyable commands with their working directory and makes no
file changes. It works before setup: executable names come from `PATH` and
`/path/to/work` is a placeholder. After setup it prints the recorded build
paths. Options can appear before or after the exercise name.
`run.sh` keeps the exercise commands inline; one small helper prints and logs
them. A final summary checks the reported residuals for the complete exercise.

## Lab 1, 20:00–30:00: convergence and restart

```bash
bash lab/run.sh 1
```

This runs one Jacobi baseline, then three Krylov methods with the same FSAI
preconditioner at two problem sizes, and a short-restart GMRES experiment.
Each solve starts from zero and requests relative tolerance `1e-8`.

The first command expands to:

```bash
"$LAP" -ns 1 -n 24 24 24 -i "$LAB/configs/pcg-jacobi.yml" -v 1
```

The `-ns 1` flag requests one solve, avoiding the mini-app's repeated-solve
default. The `-n` dimensions describe the global grid. A `24^3` grid has
13,824 unknowns; `48^3` has 110,592.

Record the iteration counts and, at 48³, the solve time:

| Method, with FSAI | 24³ iterations | 48³ iterations | 48³ solve (ms) |
|---|---:|---:|---:|
| PCG | | | |
| GMRES(30) | | | |
| BiCGSTAB | | | |
| GMRES(5), larger case only | — | | |

Questions:

1. Did every run reach the tolerance? A capped iteration count alone is not success.
2. How much does the matrix grow when each dimension doubles?
3. Does a BiCGSTAB iteration cost the same as a PCG iteration?
4. What information does GMRES discard on restart? Compare 5 with 30.

By **25:00**, have one converged solve. By **29:00**, explain the restart
comparison to a neighbor. If behind, use the named M5 reference logs for
the discussion and return to the local run later.

## Lab 2, 45:00–55:00: AMG growth and hierarchy cost

```bash
bash lab/run.sh 2
```

The first pair of runs replaces FSAI with BoomerAMG at the same two grid sizes.
The remaining runs hold the larger problem fixed and change only the number
of aggressive-coarsening levels. A representative command is:

```bash
"$LAP" -ns 1 -n 48 48 48 -i "$LAB/configs/pcg-amg.yml" -v 1 -a \
  --preconditioner:amg:print_level 1 \
  --preconditioner:amg:aggressive:num_levels 1
```

Find `Complexity: grid` and `operator` in each hierarchy printout.

| Aggressive levels | Operator complexity | Iterations | Setup (ms) | Solve (ms) | Sum (ms) |
|---|---:|---:|---:|---:|---:|
| 0 | | | | | |
| 1 | | | | | |
| 2 | | | | | |

Questions:

1. Do AMG iterations increase as much as FSAI iterations with problem growth?
2. Which hierarchy stores the least operator work?
3. Does the smallest iteration count give the best setup-plus-solve time?
4. Would your recommendation change for many right-hand sides with reusable setup?

By **50:00**, have both sizes converged. By **54:00**, choose a hierarchy
using time and convergence together. Two sizes illustrate behavior on this
problem; they do not prove asymptotic complexity or distributed scaling.

## Lab 3, 58:00–63:00: SPE10 Darcy flow with MGR

Run two policies on the original SPE10 Model 2 case 2a permeability field:

```bash
bash lab/run.sh 3
```

The mini-app uses a `30x110x85` grid sampled from the original `60x220x85`
SPE10 input. The mixed RT0/P0 system has about 1.14 million unknowns and runs
on eight MPI ranks with a `2x2x2` partition. Setup downloads the original
permeability file before class; no network access is needed during the lab.
Both configurations use GMRES and the same MGR flux/pressure split.
`darcy-mgr-default.yml` applies one AMG cycle to the reduced pressure problem;
`darcy-mgr-strong.yml` applies two.

| MGR policy | Iterations | Relative residual | Setup (ms) | Solve (ms) |
|---|---:|---:|---:|---:|
| One AMG cycle | | | | |
| Two AMG cycles | | | | |

In each configuration, `f_dofs: [1]` labels flux as F. Pressure is the
retained C field. Compare the extra coarse solve work with the GMRES iterations
it saves, and verify that both runs converge before comparing time.

## Lab 4, 68:00–83:00: a real matrix from file

```bash
bash lab/run.sh 4
```

The input is **Schmid/thermal1**, a real SPD finite-element thermal matrix from
SuiteSparse. It has 82,654 rows and 574,458 nonzeros after expanding symmetric
storage. The compressed input is bundled under `lab/data/`; setup verifies
its checksum and extracts it under `$WORK/data/`.

Every file policy contains:

```yaml
linear_system:
  type: mtx
  matrix_filename: data/thermal1.mtx
  rhs_mode: randsol
  init_guess_mode: zeros
```

`randsol` creates a deterministic reference solution and forms `b = A x_ref`.
This controlled right-hand side replaces the physical right-hand side that
the collection archive supplies separately. It is an experiment on solver
behavior, not a validation of the original thermal model. Matrix paths resolve
against the process working directory, so the runner changes into `$WORK`.
To run one policy yourself:

```bash
( cd "$WORK" && "$CLI" "$LAB/configs/file-amg.yml" )
```

The first two policies pair PCG with AMG or FSAI. The generic ILU policy uses
GMRES(50), because a generic ILU preconditioner need not satisfy PCG's SPD
requirements. All three request relative tolerance `1e-8`.

Because `randsol` knows `x_ref`, the CLI also prints `L2 norm of error` and
`L2 norm of ref. solution`. Their ratio is the relative solution error
`||x - x_ref|| / ||x_ref||`.

| Preconditioner / solver | Relative residual | Relative error | Iterations | Setup (ms) | Solve (ms) | Sum (ms) |
|---|---:|---:|---:|---:|---:|---:|
| AMG / PCG | | | | | | |
| FSAI / PCG | | | | | | |
| ILU / GMRES(50) | | | | | | |

Questions:

1. Do the metadata and loaded row count match the expected matrix?
2. Have all policies converged to the requested residual tolerance?
   Do they reach the same relative error?
3. Which setup is cheapest? Which complete solver lifecycle is cheapest?
4. For 20 right-hand sides, evaluate `setup + 20 * solve`. State the assumption
   that the matrix, policy and per-right-hand-side solve costs stay comparable.
5. What would you need to know before transferring this choice to your matrix?

By **73:00**, import the file and converge one policy. By **78:00**, record
all three. By **80:00**, write one recommendation for a single solve and one
for repeated right-hand sides. Repeat timings before interpreting close results.

## Logs, checks, and reference results

Each runner command writes raw text logs and a `summary-<exercise>.csv` under
`$WORK/out/`. `summarize.py` checks that statistics rows exist and their reported
relative residuals meet `1e-8` (allowing only the printed precision). It rejects
non-finite values and iteration-cap failures that leave a larger residual.
It also checks that the convergence history contains every reported iteration.

```bash
python3 "$LAB/summarize.py" "$WORK"/out/file-*.txt
```

The slide tables use the hypredrive v0.4.0 results in
`reference/macos-arm64-m5/`, which includes raw logs, exact revisions, toolchain
and CSV data. Use these as a fallback while your machine is building. Timings
are individual measurements on the named M5 host; validate your own residuals
and compare trends. Every solver log contains the residual at each iteration.

After Labs 1, 2, and 4, compare the 16 reference-backed logs, iteration
counts, and Lab 4 errors with the M5 reference:

```bash
python3 "$LAB/compare.py" "$WORK/out"
```

This also rejects missing cases, unconverged runs, multiple statistics rows
for a required case, invalid file-error norms and a changed Lab 4 error
ordering. Iteration differences are reported, with differences above 10%
flagged for investigation. Lab 3 has an eight-rank [M5 SPE10 reference](reference/macos-arm64-m5/spe10/README.md);
compare its iteration count and residuals, not timings across machines.
The recorded [M5 macOS profile](reference/macos-arm64-m5/README.md) contains
the validated Apple Silicon results and command wall times.

Copy any results you want to keep from `/tmp` into your own persistent results
folder before the operating system cleans temporary storage.

## Optional extensions, after the required blocks

```bash
bash lab/run.sh transport  # nonsymmetric upwind transport, GMRES + AMG
bash lab/run.sh maxwell    # same edge-element matrix, compare AMG with AMS
bash lab/run.sh mpi        # same global problem, 1/2/4 MPI ranks
```

The MPI study passes an explicit `-P ranks 1 1` processor grid. Run only as
many ranks as your machine can support. It is a small shared-machine study,
not a distributed scalability benchmark.

## Five optional SuiteSparse matrices

Three of the five suggestions are from Janna. All are real SPD matrices,
so the runner uses PCG + AMG/FSAI and GMRES(50) + ILU. Fault_639 and
Emilia_923 use unknown-based AMG with three displacement functions and
strong_th 0.8.

| Collection ID | Matrix | Rows | Numerical nonzeros | Experiment |
|---|---|---:|---:|---|
| 1883 | [McRae/ecology2](https://sparse.tamu.edu/McRae/ecology2) | 999,999 | 4,995,991 | Ecological diffusion |
| 1403 | [Schmid/thermal2](https://sparse.tamu.edu/Schmid/thermal2) | 1,228,045 | 8,580,313 | Larger thermal model |
| 2547 | [Janna/StocF-1465](https://sparse.tamu.edu/Janna/StocF-1465) | 1,465,137 | 21,005,389 | Stochastic porous flow |
| 2543 | [Janna/Fault_639](https://sparse.tamu.edu/Janna/Fault_639) | 638,802 | 27,245,944 | Fault contact mechanics |
| 2542 | [Janna/Emilia_923](https://sparse.tamu.edu/Janna/Emilia_923) | 923,136 | 40,373,538 | 3-D geomechanics |

These are after-class experiments. The Janna inputs have denser rows and need
more memory than the required thermal1 exercise. Compressed downloads range
from about 10 to 137 MB; archives and extracted inputs stay in the temporary
workspace, not the workshop repository.

```bash
python3 lab/suitesparse.py list
python3 lab/suitesparse.py run 2547   # numeric ID or Janna/StocF-1465
python3 lab/suitesparse.py run all    # attempt all five with all three policies
```

The helper needs no Python packages beyond the standard library. It downloads
from the official UF mirror, using system `curl` if Python's certificate
validation cannot use that mirror. TLS verification stays enabled. It checks
archive and Matrix Market SHA-256 hashes from `matrices.json`,
and writes raw logs, exact YAML policies, per-case JSON records and a summary
table under `$WORK/out/suitesparse/<UTC-time>/`. Download and import time are
separate from solver setup + solve. Each policy allows 1,500 iterations and
has a 600-second wall-time limit, adjustable with `--timeout SECONDS`.
It prints each hypredrive-cli command and a summary table after the selected
matrix run.

An unconverged solve or timeout is recorded and makes the final command exit
nonzero; the runner continues to record the remaining policies. A lower
iteration count is not evidence of success. Keep these cases when discussing
which default policies need tuning for another operator.

```bash
# Keep results in a persistent folder of your choice:
python3 lab/suitesparse.py run all --results /path/to/my-results
# Continue an interrupted run with unchanged settings and retain prior cases:
python3 lab/suitesparse.py run all --results /path/to/my-results --resume
# Rebuild the table and CSV from the saved per-case records:
python3 lab/suitesparse.py report /path/to/my-results
```

The [recorded M5 comparison](reference/macos-arm64-m5/suitesparse/README.md)
contains all five matrices with their exact policies. Its individual timings
are reference evidence for that host, not expected student laptop times.
Fault_639 and Emilia_923 store explicit zeros; the catalog records both
numerical nonzeros and expanded entries.

## Troubleshooting

| Symptom | Action |
|---|---|
| `mpicc` or CMake missing | Finish the prerequisite installation before setup |
| Apple Silicon architecture mismatch | Use native Terminal and a consistent native compiler/MPI installation |
| `mpiexec` launches the wrong MPI | Put the installation matching `mpicc` first in `PATH` |
| Matrix file not found | Use `run.sh 3`, or run the CLI from `$WORK` |
| Build path disappeared | Run `setup.sh` again, then source `activate.sh` again |
| Build interrupted | Use `setup.sh --reuse` if the source directory still exists |
| Nonconvergence or missing statistics | Keep the raw log, check the pinned versions and policy; use reference data for the timed discussion |
| Laptop busy or hot | Stop optional runs and use the smaller required sizes; avoid comparing timing with another machine |
