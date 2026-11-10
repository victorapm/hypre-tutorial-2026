# Linux arm64 container validation

Recorded 2026-11-13 with hypredrive v0.4.0 and hypre v3.2.1.
Native arm64 Linux container on an Apple M5 Max Colima VM,
two virtual CPUs and 2 GiB RAM. Clang 18, Open MPI 4.1.6, CPU Release,
OpenMP and accelerators disabled, one thread per rank. Source/toolchain
metadata is in environment.json; image ID, executable hashes, VM resources
and emulation status are in runtime.json.

All four labs passed. Root summary.csv contains 24 solve records for Labs 1,
2 and 4, transport, Maxwell and the optional 1/2/4-rank MPI study.
[Lab 3 SPE10/MGR](spe10/README.md) adds two eight-rank solves;
[parallel MTX](mtx-mpi/README.md) adds one two-rank thermal1 solve.
Each record includes a raw log. The MPI cases with four/eight ranks
oversubscribe this VM. Use the logs to compare residual reduction and solver costs. Setup plus solve excludes import and
assembly; file cases use manufactured reference solutions.

From the repository root, validate the main logs against the current M5
reference, or run the complete container checks:

```bash
python3 lab/compare.py lab/reference/linux-arm64-container-m5
bash container/test.sh
```
