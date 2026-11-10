"""Check that each solver log retains every iteration's residual."""
import math
import re

NUMBER = r"(?:[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[+-]?inf|nan)"
ROW = re.compile(rf"^\s*(\d+)\s+({NUMBER})\s+({NUMBER})(?:\s+({NUMBER}))?\s*$", re.I)


def check_history(text, iterations):
    histories = []
    current = None
    for line in text.splitlines():
        if re.match(r"^\s*Iters\b", line):
            current = []
            histories.append(current)
        elif current is not None:
            match = ROW.match(line)
            if match:
                values = [float(value) for value in match.groups()[1:] if value is not None]
                if not all(math.isfinite(value) and value >= 0 for value in values):
                    raise ValueError("Invalid convergence-history residual or rate")
                current.append(int(match[1]))
            elif re.match(r"^\s*(?:Final |L2 norm|STATISTICS|={5,})", line):
                current = None
    if len(histories) != len(iterations):
        raise ValueError("Missing convergence history; set solver print_level: 2")
    for solve, (history, count) in enumerate(zip(histories, iterations), 1):
        if history and history[0] == 0:
            history = history[1:]
        if history != list(range(1, count + 1)):
            raise ValueError(f"Solve {solve}: incomplete convergence history for {count} iterations")


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    args = parser.parse_args()
    solves = total = 0
    for path in args.logs:
        text = path.read_text()
        counts = [int(line.split("|")[-2].strip()) for line in text.splitlines()
                  if re.match(r"^\|\s*\d+(?:\.\d+)?\s*\|", line)]
        try:
            if not counts:
                raise ValueError("No solve statistics")
            check_history(text, counts)
        except ValueError as error:
            parser.exit(1, f"{path}: {error}\n")
        solves += len(counts)
        total += sum(counts)
    print(f"Complete convergence histories: {solves} solves, {total} iterations.")
