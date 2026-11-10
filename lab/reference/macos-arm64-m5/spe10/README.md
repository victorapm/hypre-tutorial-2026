# SPE10 Darcy/MGR reference run

Recorded 2026-11-13 on Apple M5 Max with hypredrive v0.4.0 and hypre v3.2.1.
The original 60x220x85 SPE10 field is sampled on a 30x110x85 grid, giving
1,137,200 mixed RT0/P0 unknowns (856,700 flux and 280,500 pressure).
Eight CPU MPI ranks use a 2x2x2 processor grid and one thread per rank.

| MGR policy | AMG cycles | GMRES iterations | Relative residual | Setup (ms) | Solve (ms) | Total (ms) |
|---|---:|---:|---:|---:|---:|---:|
| One AMG cycle | 1 | 23 | 9.97e-11 | 66.997 | 156.713 | 223.710 |
| Two AMG cycles | 2 | 19 | 9.19e-11 | 62.046 | 188.362 | 250.408 |

Both runs meet the requested 1e-10 relative-residual tolerance.
Times are individual measurements on this host and exclude data setup and assembly.
Input checksums, source revisions and policy hashes are in environment.json; the permeability input is not stored here.
