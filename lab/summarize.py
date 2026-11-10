"""Read actual statistics rows and reject missing or unconverged results."""
import argparse
import csv
import math
import re
from pathlib import Path
from convergence import check_history

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("logs", nargs="+", type=Path)
parser.add_argument("--csv", type=Path)
args = parser.parse_args()
rows = []
failed = []
for path in args.logs:
    iterations_in_log = []
    text = path.read_text(errors="replace")
    matches = [line for line in text.splitlines() if re.match(r"^\|\s*\d+(?:\.\d+)?\s*\|", line)]
    if not matches:
        failed.append(f"{path}: no statistics rows")
    for line in matches:
        fields = [v.strip() for v in line.split("|")[1:-1]]
        if len(fields) != 7:
            failed.append(f"{path}: unexpected table row {line}")
            continue
        try:
            entry = float(fields[0])
            # Preserve an unavailable LS build time as a missing value.
            assembly = float(fields[1]) if fields[1] not in ('', '-', '--', 'N/A') else None
            setup, solve, initial, residual, iterations = map(float, fields[2:])
        except ValueError:
            failed.append(f"{path}: nonnumeric statistics row")
            continue
        values = (entry, setup, solve, initial, residual, iterations)
        if not all(math.isfinite(v) for v in values) or residual < 0 or residual > 1.005e-8:
            failed.append(f"{path}: relative residual {residual} exceeds 1e-8 or is invalid")
        rows.append(dict(case=path.stem, entry=fields[0], iterations=int(iterations),
                         setup_ms=setup, solve_ms=solve, total_ms=round(setup + solve, 3),
                         assembly_ms=assembly, relative_residual=residual))
        iterations_in_log.append(int(iterations))
    if iterations_in_log:
        try:
            check_history(text, iterations_in_log)
        except ValueError as error:
            failed.append(f"{path}: {error}")
if rows:
    print(f"{'case':36s} {'it':>5s} {'setup ms':>10s} {'solve ms':>10s} {'sum ms':>10s} {'rel res':>10s}")
    for row in rows:
        print(f"{row['case']:36s} {row['iterations']:5d} {row['setup_ms']:10.3f} "
              f"{row['solve_ms']:10.3f} {row['total_ms']:10.3f} {row['relative_residual']:10.2e}")
if args.csv and rows:
    with args.csv.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
if failed:
    raise SystemExit("\n".join(failed))
