# Parallel Matrix Market container result

hypredrive v0.4.0 and hypre v3.2.1 loaded Schmid/thermal1 on two MPI ranks:
82,654 rows and 574,458 expanded entries. The solve converged below 1e-8 and
exited successfully with no MPI shutdown error. Raw logs, summary.csv,
exact policy and checksums accompany this record.

From the repository root:

```bash
bash container/run.sh shell -c 'cd "$WORK" && mpiexec -n 2 "$CLI" "$LAB/configs/file-amg.yml"'
```
