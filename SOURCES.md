# Sources and data provenance

Stanford 2026 workshop by Victor A. P. Magri, Center for Applied Scientific
Computing, LLNL. The PDF carries LLNL-PRES-2026854. Its closing slide includes the complete
LLNL auspices, funding acknowledgment and disclaimer.

## Software and recorded measurements

The required workshop path contains four CPU labs. Lab 3 uses SPE10 case 2a,
sampled from its 60x220x85 permeability field to a 30x110x85 mixed Darcy grid
(about 1.14 million unknowns) on eight MPI ranks with a 2x2x2 partition.
Setup downloads the input through hypredrive's pinned helper. Its two MGR
policies keep the same flux/pressure split and compare one with two AMG cycles.
The M5 reference logs are in [the SPE10 Lab 3 results](lab/reference/macos-arm64-m5/spe10/README.md).
Lab 4 uses the real Schmid/thermal1 matrix.

- [hypredrive](https://github.com/hypre-space/hypredrive), v0.4.0, pinned commit
  `9ffb54a2621e454f7c060d11b9667f08a0085060`
- [hypre](https://github.com/hypre-space/hypre), v3.2.1, resolved commit
  `c3feb783b21b3465e30c29e883325aa766a5b8f4`
- [hypre documentation](https://hypre.readthedocs.io)
- [hypredrive documentation](https://hypredrive.readthedocs.io)

Current slide and lab references were measured on Apple M5 Max macOS with
hypredrive v0.4.0 on 2026-11-13, including SPE10/MGR and parallel Matrix Market
validation. The optional five-matrix comparison has 14 converged policies out
of 15 attempts; Fault_639 with ILU remains above tolerance at the iteration cap.
Host and toolchain details accompany each profile. The backup CPU/A100
table uses the aggregate data in lab/reference/polaris-cpu-a100/.

The container profiles record the same release on Linux arm64 and amd64
under Colima. The amd64 measurements are emulated; each profile records
the image ID, compiler/MPI versions, executable hashes and VM resources.

## SuiteSparse inputs

The required `Schmid/thermal1` input (ID 1402) is bundled compressed with its
SHA-256 checksum. Its [data README](lab/data/README.md) gives provenance.

The optional matrices are fetched separately; their large archives and
extracted inputs are not stored in this repository. `lab/matrices.json`
records collection IDs, official download URLs, matrix classes, dimensions,
explicit-zero counts, and both archive and Matrix Market checksums:

- [McRae/ecology2, ID 1883](https://sparse.tamu.edu/McRae/ecology2)
- [Schmid/thermal2, ID 1403](https://sparse.tamu.edu/Schmid/thermal2)
- [Janna/StocF-1465, ID 2547](https://sparse.tamu.edu/Janna/StocF-1465)
- [Janna/Fault_639, ID 2543](https://sparse.tamu.edu/Janna/Fault_639)
- [Janna/Emilia_923, ID 2542](https://sparse.tamu.edu/Janna/Emilia_923)

Metadata and Matrix Market archives were retrieved from the collection's
official University of Florida mirror on 2026-11-11. All five are real SPD
matrices. Fault_639 and Emilia_923 use unknown-based AMG with three functions
and strong_th 0.8; their exact configurations and stored-zero counts are in
lab/matrices.json and the saved policy files.

The comparisons manufacture a deterministic reference solution and form
`b = A x_ref`. They evaluate solver behavior, not the collection's original
physical right-hand sides or application validation.

Collection citation: T. A. Davis and Y. Hu, *The University of Florida Sparse
Matrix Collection*, ACM Transactions on Mathematical Software 38(1), 2011,
[doi:10.1145/2049662.2049663](https://doi.org/10.1145/2049662.2049663).
