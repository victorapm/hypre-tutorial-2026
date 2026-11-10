# Parallel Matrix Market reference runs

Recorded on Apple M5 Max with hypredrive v0.4.0, hypre v3.2.1 and MPICH 5.0.2.
Each run uses one thread per rank, a manufactured randsol right-hand side and zero initial guess.

| Case | MPI ranks | Rows | Expanded entries | Iterations | Relative residual | Setup + solve (ms) |
|---|---:|---:|---:|---:|---:|---:|
| fault-fsai-8 | 8 | 638,802 | 28,614,564 | 1342 | 9.86e-09 | 8757.353 |
| thermal1-amg-2 | 2 | 82,654 | 574,458 | 9 | 2.01e-09 | 91.371 |

Both runs met 1e-8 and exited with status zero, with no MPI_Finalize abort.
Fault_639 includes 1,368,620 explicit zero entries in its expanded storage.
The row partition changes the FSAI preconditioner and its iteration count.
These timings are individual validation measurements, not a scaling benchmark.

After setup, fetch Fault_639 and run from the workshop root:

```bash
python3 lab/suitesparse.py fetch 2543
source lab/activate.sh
(cd "$WORK" && mpiexec -n 2 "$CLI" "$LAB/reference/macos-arm64-m5/mtx-mpi/policies/thermal1-amg-2.yml")
(cd "$WORK" && mpiexec -n 8 "$CLI" "$LAB/reference/macos-arm64-m5/mtx-mpi/policies/fault-fsai-8.yml")
```
