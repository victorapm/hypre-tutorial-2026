# Exploring Scalable Linear Solvers with hypre and hypredrive

90-minute workshop with four CPU labs: Krylov methods, AMG tuning,
Darcy/MGR, and a real SuiteSparse matrix. Uses hypredrive **v0.4.0** and hypre **v3.2.1**.
[Slides](Stanford26.pdf) · [Lab guide](lab/README.md) ·
[Reference answers](lab/ANSWERS.md)

## Quick start

Run these commands from the repository folder.

**Native:** install the [prerequisites](lab/README.md#before-class), then run:

```bash
bash lab/setup.sh --jobs 4
bash lab/run.sh 1
bash lab/run.sh 2
bash lab/run.sh 3
bash lab/run.sh 4
```

**Container:** use Docker Engine on Linux, Docker Desktop/Colima on macOS, or
Docker Desktop with WSL2 on Windows. Follow the [platform instructions](container/README.md):

```bash
bash container/run.sh 1
```

## Labs

| Lab | Topic |
|---|---|
| `1` | Krylov methods and GMRES restart |
| `2` | AMG growth and coarsening |
| `3` | Darcy flow with MGR |
| `4` | A real SuiteSparse matrix: AMG, FSAI, and ILU |

Replace `1` above with `2`, `3`, `4`, or `all`. Use `--dry` to preview
commands and `-h` for help.

Try the [five optional matrices](lab/README.md#five-optional-suitesparse-matrices),
including three Janna cases, and compare with the [v0.4.0 M5 results](lab/reference/macos-arm64-m5/README.md).
The M5 SPE10/MGR Lab 3 reference is in [lab/reference/macos-arm64-m5/spe10/](lab/reference/macos-arm64-m5/spe10/).
Native outputs live under `/tmp`; container outputs stay in `results/container/`.
Save native results you want to keep.

## Project layout

```text
.
├── Stanford26.pdf          # Presentation
├── lab/
│   ├── ANSWERS.md          # Expandable reference answers
│   ├── README.md            # Setup and exercises
│   ├── setup.sh            # Native installation
│   ├── run.sh              # Exercise commands
│   ├── convergence.py      # Check complete iteration histories
│   ├── configs/            # Solver policies (YAML)
│   ├── data/               # Bundled thermal1 input
│   ├── reference/          # Saved logs, CSVs, and comparisons
│   └── suitesparse.py      # Optional matrix experiments
├── container/              # Docker/Colima launcher and guide
├── Dockerfile              # Builds the solver image
├── .github/workflows/      # Container builds and tests
├── COPYRIGHT               # Copyright and third-party scope
├── LICENSE                 # MIT license for original tutorial material
└── SOURCES.md              # Data provenance and citations
```

## References

1. Robert D. Falgout and Ulrike Meier Yang.
   [hypre: A Library of High Performance Preconditioners](https://doi.org/10.1007/3-540-47789-6_66).
   Computational Science—ICCS 2002, pp. 632–641, 2002.
   Report number: UCRL-JC-146175.

2. Victor A. P. Magri.
   [Hypredrive: High-level interface for solving linear systems with hypre](https://doi.org/10.21105/joss.06654).
   Journal of Open Source Software, 9(98), article 6654, 2024.
   Report number: N/A.

## License and copyright

Original tutorial materials are distributed under the MIT License. See
[LICENSE](LICENSE) and [COPYRIGHT](COPYRIGHT). Third-party software, data,
and artwork retain their respective terms as described in [SOURCES.md](SOURCES.md).
