"""Validate reference-backed Labs 1, 2, and 4 and compare with a named reference host.

Run after Labs 1, 2 and 4. Lab 3 SPE10/MGR has a separate eight-rank M5
reference. Timings are individual measurements; this comparison does not
compute speedups between machines.
"""
import argparse
import csv
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path


LAB = Path(__file__).resolve().parent
CASES = (
    "krylov-n24-pcg-jacobi",
    "krylov-n24-pcg-fsai", "krylov-n24-gmres-fsai", "krylov-n24-bicgstab-fsai",
    "krylov-n48-pcg-fsai", "krylov-n48-gmres-fsai", "krylov-n48-bicgstab-fsai",
    "krylov-n48-gmres-fsai-k5",
    "amg-n24", "amg-n48", "amg-agg0", "amg-agg1", "amg-agg2",
    "file-amg", "file-fsai", "file-ilu",
)


def statistics(folder):
    logs = [folder / f"{case}.txt" for case in CASES]
    missing = [str(path) for path in logs if not path.is_file()]
    if missing:
        raise ValueError("Missing required logs:\n" + "\n".join(missing))
    # Use the same residual validation as the runner, reading raw logs rather
    # than trusting a CSV that could belong to an earlier run.
    with tempfile.TemporaryDirectory(prefix="stanford26-compare-") as tmp:
        summary = Path(tmp) / "summary.csv"
        result = subprocess.run(
            [sys.executable, str(LAB / "summarize.py"), *map(str, logs),
             "--csv", str(summary)], capture_output=True, text=True,
        )
        if result.returncode:
            raise ValueError(result.stderr.strip())
        with summary.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
    if len(rows) != len(CASES) or {row["case"] for row in rows} != set(CASES):
        raise ValueError(f"{folder}: expected one statistics row per required case")
    return {row["case"]: row for row in rows}


def relative_error(folder, policy):
    path = folder / f"file-{policy}.txt"
    text = path.read_text(errors="replace")
    values = []
    for label in ("L2 norm of error", "L2 norm of ref. solution"):
        matches = re.findall(r"^" + re.escape(label) + r":\s*(\S+)", text, re.M)
        if len(matches) != 1:
            raise ValueError(f"{path}: expected one {label}")
        values.append(float(matches[0]))
    error, norm = values
    if not all(math.isfinite(value) for value in values) or error < 0 or norm <= 0:
        raise ValueError(f"{path}: invalid solution-error norms")
    ratio = error / norm
    if not math.isfinite(ratio):
        raise ValueError(f"{path}: non-finite relative solution error")
    return ratio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="folder containing the raw lab logs")
    parser.add_argument("--reference", type=Path, default=LAB / "reference/macos-arm64-m5")
    args = parser.parse_args()
    try:
        actual = statistics(args.results)
        reference = statistics(args.reference)
        errors = {p: relative_error(args.results, p) for p in ("amg", "fsai", "ilu")}
        reference_errors = {p: relative_error(args.reference, p) for p in errors}
        print(f"Results: {args.results}\nReference: {args.reference}")
        print(f"{'case':30s} {'it':>5s} {'ref it':>6s} {'rel res':>10s} "
              f"{'sum ms':>10s} {'ref sum ms':>10s}")
        differences = []
        for case in CASES:
            row, ref = actual[case], reference[case]
            iterations, ref_iterations = int(row["iterations"]), int(ref["iterations"])
            flag = ""
            if iterations != ref_iterations:
                differences.append(case)
                flag = "  iterations differ"
                if abs(iterations - ref_iterations) > 0.1 * ref_iterations:
                    flag += " by more than 10%; investigate before class"
            print(f"{case:30s} {iterations:5d} {ref_iterations:6d} "
                  f"{float(row['relative_residual']):10.2e} "
                  f"{float(row['total_ms']):10.3f} {float(ref['total_ms']):10.3f}{flag}")
        for policy, error in errors.items():
            print(f"file-{policy}: relative error {error:.2e}; "
                  f"reference {reference_errors[policy]:.2e}")
        if not errors["amg"] < errors["fsai"] < errors["ilu"]:
            raise ValueError("Lab 4 error ordering differs from AMG < FSAI < ILU; "
                             "review the file-accuracy slide before class")
        print(f"Validated {len(CASES)} reference-backed Lab 1, 2, and 4 solves; "
              f"cases with different iteration counts: {len(differences)}.")
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
