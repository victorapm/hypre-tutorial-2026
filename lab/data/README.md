# Matrix input

`thermal1.mtx.gz` is a gzip-compressed, otherwise unchanged copy of
`thermal1/thermal1.mtx` from the SuiteSparse Matrix Collection.

- Matrix: [Schmid/thermal1](https://sparse.tamu.edu/Schmid/thermal1), ID 1402
- Author: D. Schmid, University of Oslo. Editor: T. Davis. Date: 2006.
- Description: unstructured finite elements, steady thermal problem
- Collection metadata: real, symmetric positive definite, 82,654 rows,
  574,458 nonzeros after expanding symmetry
- File: 328,556 stored lower-triangular entries including the diagonal.
  Matrix Market readers expand the declared symmetric storage.
- Original archive: https://www.cise.ufl.edu/research/sparse/MM/Schmid/thermal1.tar.gz
- Retrieved: 2026-11-09. The gzip uses `gzip -n` for reproducible metadata.
- Integrity: `thermal1.mtx.gz.sha256`. `prepare.py` verifies it before extraction.

The class uses a manufactured right-hand side (`rhs_mode: randsol`) to hold
the experiment constant across solver policies. It does not use the physical
right-hand side supplied separately in the collection archive.

Collection citation: T. A. Davis and Y. Hu, The University of Florida Sparse
Matrix Collection, ACM Transactions on Mathematical Software 38(1), 2011,
[doi:10.1145/2049662.2049663](https://doi.org/10.1145/2049662.2049663).

## SPE10 case 2a for Lab 3

Native setup downloads the original SPE10 Model 2 case 2a archive using the
helper in the pinned hypredrive source:
`https://www.spe.org/web/csp/datasets/por_perm_case2a.zip`. The Darcy mini-app
uses `spe_perm.dat`, with the 60x220x85 field sampled onto a 30x110x85 grid.
The input is stored only in the temporary workspace. The container image
includes the permeability file so Lab 3 runs offline.
