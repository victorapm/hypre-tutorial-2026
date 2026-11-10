# Optional SuiteSparse results

Recorded 2026-11-13 on Apple M5 Max with hypredrive v0.4.0 and hypre v3.2.1.

CPU Release, one MPI rank, one thread, manufactured `randsol` RHS and zero initial guess.
PCG + AMG/FSAI; GMRES(50) + ILU. Tolerance 1e-8, at most 1,500 iterations.
Exact YAML policies retain any matrix-specific AMG settings.
These are individual measurements on the host in `environment.json`; repeat close timings.
Input download and import are excluded from setup + solve. Matrix archives are fetched separately.
Failures and timeouts are retained alongside successful solves.

| Matrix / ID | Policy | Status | Iterations | Relative residual | Relative error | Setup + solve (ms) |
|---|---|---|---:|---:|---:|---:|
| Schmid/thermal2 / 1403 | amg | converged | 8 | 8.54e-09 | 4.07e-07 | 1889.774 |
| Schmid/thermal2 / 1403 | fsai | converged | 521 | 9.94e-09 | 2.34e-04 | 19636.962 |
| Schmid/thermal2 / 1403 | ilu | converged | 606 | 9.99e-09 | 1.21e-03 | 28488.525 |
| McRae/ecology2 / 1883 | amg | converged | 7 | 1.73e-09 | 1.20e-08 | 620.877 |
| McRae/ecology2 / 1883 | fsai | converged | 455 | 9.81e-09 | 4.63e-04 | 7984.740 |
| McRae/ecology2 / 1883 | ilu | converged | 298 | 9.92e-09 | 1.21e-03 | 8528.539 |
| Janna/Emilia_923 / 2542 | amg | converged | 18 | 4.71e-09 | 8.93e-06 | 4319.098 |
| Janna/Emilia_923 / 2542 | fsai | converged | 489 | 9.90e-09 | 2.85e-04 | 27886.880 |
| Janna/Emilia_923 / 2542 | ilu | converged | 102 | 9.92e-09 | 6.99e-04 | 7926.619 |
| Janna/Fault_639 / 2543 | amg | converged | 24 | 7.51e-09 | 1.65e-05 | 3884.557 |
| Janna/Fault_639 / 2543 | fsai | converged | 226 | 9.82e-09 | 1.62e-04 | 11948.614 |
| Janna/Fault_639 / 2543 | ilu | unconverged | 1500 | 1.56e-05 | 5.52e-02 | 75517.808 |
| Janna/StocF-1465 / 2547 | amg | converged | 10 | 5.17e-09 | 1.55e-05 | 2157.107 |
| Janna/StocF-1465 / 2547 | fsai | converged | 328 | 9.78e-09 | 1.13e-02 | 19146.822 |
| Janna/StocF-1465 / 2547 | ilu | converged | 69 | 9.97e-09 | 9.04e-02 | 4457.078 |

Raw outputs: `<ID>-<policy>.txt`; per-case records: `<ID>-<policy>.json`.
`policies/` retains the exact YAML inputs and each JSON record includes input/policy/log SHA-256 checksums.
Download URLs, Matrix Market checksums, dimensions and explicit-zero counts are in `lab/matrices.json`.
Fault_639 and Emilia_923 contain explicit zeros; see lab/matrices.json for exact counts.

From the workshop root, reproduce a case after setup:

```bash
python3 lab/suitesparse.py list
python3 lab/suitesparse.py run 2547
```

Use `run all` to attempt the complete list. A nonzero exit means a retained failed solve or timeout.
`report RESULTS_DIR` regenerates this table and CSV from the per-case JSON records.
