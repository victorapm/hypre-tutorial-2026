# SPE10/MGR container results

hypredrive v0.4.0 and hypre v3.2.1. The 30x110x85 mixed Darcy grid has
1,137,200 unknowns. Eight ranks use a 2x2x2 MPI partition and one thread each.
Both MGR policies converged below 1e-10. Raw logs and summary.csv retain the
iterations and setup/solve times; environment.json records input and policy
hashes. This oversubscribes the two-CPU Colima VM; timings are validation
measurements, not scaling results.

From the repository root:

```bash
bash container/run.sh 3
```
