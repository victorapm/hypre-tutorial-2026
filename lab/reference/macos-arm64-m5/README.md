# macOS reference runs

Apple M5 Max, macOS arm64, hypredrive v0.4.0 and hypre v3.2.1.
Recorded 2026-11-13, CPU Release, one thread per rank.
Host, toolchain, source revisions and policy hashes are in environment.json.

Every solve log contains the residual at each iteration and a statistics
summary. summary.csv records setup, solve, iterations and final residual.

- [SPE10/MGR](spe10/README.md): eight ranks on a 2x2x2 grid.
- [SuiteSparse](suitesparse/README.md): five matrices, three policies each.
- [Parallel MTX](mtx-mpi/README.md): thermal1 on two ranks and Fault_639 on eight.

From the tutorial root:

```bash
python3 lab/compare.py lab/reference/macos-arm64-m5
```
