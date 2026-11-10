"""Fetch and compare the five optional SuiteSparse matrices with the lab policies.

Uses only Python's standard library. Run setup first, then:
  python3 lab/suitesparse.py list
  python3 lab/suitesparse.py run 2547
  python3 lab/suitesparse.py run all
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from convergence import check_history
import platform
import re
import shlex
import shutil
import signal
import ssl
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.request import urlopen
from urllib.error import URLError

LAB = Path(__file__).resolve().parent
POLICIES = ("amg", "fsai", "ilu")


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def verify(path, expected):
    if digest(path) != expected:
        raise ValueError(f"Checksum mismatch: {path}. Restore this cached input before retrying.")


def catalog():
    return json.loads((LAB / "matrices.json").read_text())["matrices"]


def select(value):
    matrices = catalog()
    if value == "all":
        return matrices
    selected = [m for m in matrices if value in
                (str(m["id"]), f"{m['group']}/{m['name']}")]
    if not selected:
        raise ValueError("Choose a matrix ID or Group/Name from 'suitesparse.py list'.")
    return selected


def workspace(value=None):
    if value:
        return Path(value).expanduser().resolve()
    if os.environ.get("WORK"):
        return Path(os.environ["WORK"]).resolve()
    recorded = LAB / ".build-path"
    if recorded.is_file():
        return Path(recorded.read_text().strip()) / "work"
    raise ValueError("Run bash lab/setup.sh first, or pass --work DIR.")


def fetch(matrix, work):
    folder = work / "data/suitesparse" / str(matrix["id"])
    folder.mkdir(parents=True, exist_ok=True)
    archive, target = folder / "matrix.tar.gz", folder / "matrix.mtx"
    if not archive.exists():
        partial = folder / "matrix.tar.gz.part"
        print(f"Downloading {matrix['group']}/{matrix['name']} "
              f"({matrix['archive_bytes'] / 1e6:.1f} MB)", flush=True)
        try:
            with urlopen(matrix["archive_url"], timeout=60) as source, partial.open("wb") as dest:
                shutil.copyfileobj(source, dest, 1024 * 1024)
        except URLError as error:
            # Homebrew Python's stricter X.509 validation can reject the legacy
            # mirror's certificate while macOS's native trust store accepts it.
            # Use the system downloader with TLS verification still enabled.
            curl = shutil.which("curl")
            if not isinstance(error.reason, ssl.SSLCertVerificationError) or not curl:
                raise
            result = subprocess.run([curl, "--location", "--fail", "--silent", "--show-error",
                                     "--retry", "2", "--connect-timeout", "15", "--max-time", "900",
                                     "--output", str(partial), matrix["archive_url"]])
            if result.returncode:
                raise ValueError(f"Download failed: {matrix['archive_url']}") from error
        verify(partial, matrix["archive_sha256"])
        partial.replace(archive)
    else:
        verify(archive, matrix["archive_sha256"])
    if not target.exists():
        partial = folder / "matrix.mtx.part"
        # Extract only the named matrix, never archive paths or auxiliary files.
        with tarfile.open(archive, "r:gz") as tar:
            member = tar.getmember(f"{matrix['name']}/{matrix['name']}.mtx")
            if not member.isfile():
                raise ValueError("The archive's matrix is not a regular file.")
            with tar.extractfile(member) as source, partial.open("wb") as dest:
                shutil.copyfileobj(source, dest, 1024 * 1024)
        verify(partial, matrix["matrix_sha256"])
        partial.replace(target)
    else:
        verify(target, matrix["matrix_sha256"])
    with target.open() as stream:
        header = stream.readline().strip().lower()
        dimensions = next(line for line in stream if line.strip() and not line.startswith("%"))
    expected = (matrix["rows"], matrix["rows"], matrix["stored_entries"])
    if header != "%%matrixmarket matrix coordinate real symmetric" or \
            tuple(map(int, dimensions.split())) != expected:
        raise ValueError(f"Matrix Market header differs from the catalog: {target}")
    return target


def tool_version(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return "\n".join(result.stdout.splitlines()[:3]).strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"


def environment(args):
    settings = {}
    for line in (LAB / "versions.env").read_text().splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            settings[key] = value
    info = dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
                platform=platform.platform(), architecture=platform.machine(),
                cpu_count=os.cpu_count(), python=platform.python_version(),
                compiler=tool_version(["clang", "--version"]),
                mpi=tool_version(["mpiexec", "--version"]),
                cmake=tool_version(["cmake", "--version"]), source_pins=settings,
                catalog_sha256=digest(LAB / "matrices.json"),
                build="CPU Release; OpenMP and accelerators disabled",
                mpi_ranks=1, threads=1, max_iterations=1500,
                relative_tolerance=1e-8, timeout_seconds=args.timeout,
                rhs_mode="randsol", initial_guess="zeros",
                policies={p: digest(LAB / f"configs/file-{p}.yml") for p in POLICIES})
    if platform.system() == "Darwin":
        info["cpu"] = tool_version(["sysctl", "-n", "machdep.cpu.brand_string"])
        info["memory_bytes"] = tool_version(["sysctl", "-n", "hw.memsize"])
    build_info = os.environ.get("HYPRE_TUTORIAL_BUILD_INFO")
    if build_info:
        info["container_build"] = json.loads(Path(build_info).read_text())
    return info


def stop(process):
    # A timeout applies to this solve and any children it starts.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def read_result(path, matrix):
    with tempfile.TemporaryDirectory(prefix="stanford26-suite-summary-") as tmp:
        summary = Path(tmp) / "summary.csv"
        check = subprocess.run([sys.executable, str(LAB / "summarize.py"), str(path),
                                "--csv", str(summary)], capture_output=True, text=True)
        if not summary.is_file():
            raise ValueError(check.stderr.strip() or "Missing solver statistics")
        with summary.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
    if len(rows) != 1:
        raise ValueError("Expected exactly one solve statistics row")
    row = rows[0]
    text = path.read_text(errors="replace")
    check_history(text, [int(row["iterations"])])
    loaded = re.search(r"Solving linear system #0 with (\d+) rows and (\d+) nonzeros", text)
    if not loaded or tuple(map(int, loaded.groups())) != \
            (matrix["rows"], matrix["expanded_entries"]):
        raise ValueError("Loaded matrix dimensions/entries differ from the catalog")
    norms = []
    for label in ("L2 norm of error", "L2 norm of ref. solution"):
        matches = re.findall(r"^" + re.escape(label) + r":\s*(\S+)", text, re.M)
        if len(matches) != 1:
            raise ValueError(f"Missing or repeated {label}")
        norms.append(float(matches[0]))
    if not all(math.isfinite(v) for v in norms) or norms[0] < 0 or norms[1] <= 0:
        raise ValueError("Invalid solution-error norms")
    error = norms[0] / norms[1]
    if not math.isfinite(error):
        raise ValueError("Non-finite relative solution error")
    values = {key: float(row[key]) if row[key] else None for key in
              ("relative_residual", "setup_ms", "solve_ms", "total_ms", "assembly_ms")}
    if any(v is not None and (not math.isfinite(v) or v < 0) for v in values.values()):
        raise ValueError("Invalid solver statistics")
    values.update(iterations=int(row["iterations"]), relative_error=error)
    return values, check.returncode == 0


def run_case(matrix, policy, cli, work, results, timeout):
    label = f"{matrix['id']}-{policy}"
    config = results / "policies" / f"{label}.yml"
    template = (LAB / f"configs/file-{policy}.yml").read_text()
    original = "matrix_filename: data/thermal1.mtx"
    if template.count(original) != 1:
        raise ValueError("The file policy template's matrix path changed")
    template = template.replace(original,
                                f"matrix_filename: data/suitesparse/{matrix['id']}/matrix.mtx")
    options = matrix.get("amg_options", {}) if policy == "amg" else {}
    if not isinstance(options, dict) or set(options) - {"num_functions", "strong_th"}:
        raise ValueError(f"Invalid AMG options for matrix {matrix['id']}")
    if options:
        lines = ["preconditioner:", "  amg:", "    coarsening:"]
        if "num_functions" in options:
            functions = options["num_functions"]
            if type(functions) is not int or functions < 1:
                raise ValueError(f"Invalid AMG num_functions for matrix {matrix['id']}")
            lines.append(f"      num_functions: {functions}")
        if "strong_th" in options:
            strength = options["strong_th"]
            if (isinstance(strength, bool) or not isinstance(strength, (int, float)) or
                    not math.isfinite(strength) or not 0.0 <= strength <= 1.0):
                raise ValueError(f"Invalid AMG strong_th for matrix {matrix['id']}")
            lines.append(f"      strong_th: {strength:.15g}")
        marker = "preconditioner: amg"
        if template.count(marker) != 1:
            raise ValueError("The file AMG policy template changed")
        template = template.replace(marker, "\n".join(lines))
    config.write_text(template)
    log = results / f"{label}.txt"
    row = dict(matrix_id=matrix["id"], matrix=f"{matrix['group']}/{matrix['name']}",
               policy=policy, solver="GMRES(50)" if policy == "ilu" else "PCG",
               status="error", iterations=None, relative_residual=None, relative_error=None,
               setup_ms=None, solve_ms=None, total_ms=None, assembly_ms=None,
               policy_sha256=digest(config), input_sha256=matrix["matrix_sha256"])
    runtime = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   VECLIB_MAXIMUM_THREADS="1")
    start = time.perf_counter()
    command = (f"(cd {shlex.quote(str(work))} && {shlex.quote(str(cli))} "
               f"{shlex.quote(str(config))})")
    print(f"Running {row['matrix']} / {policy}\n+ {command}", flush=True)
    timed_out = False
    with log.open("w") as stream:
        process = subprocess.Popen([str(cli), str(config)], cwd=work, env=runtime,
                                   stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            stop(process)
    row.update(wall_seconds=round(time.perf_counter() - start, 3),
               exit_code=process.returncode, log_sha256=digest(log))
    try:
        values, converged = read_result(log, matrix)
        row.update(values)
        row["status"] = "converged" if converged else "unconverged"
    except ValueError as error:
        row["message"] = str(error)
    if timed_out:
        row["status"] = "timeout"
    elif process.returncode:
        row["status"] = "error"
    (results / f"{label}.json").write_text(json.dumps(row, indent=2) + "\n")
    print(f"  {row['status']}; iterations={row['iterations']}; "
          f"residual={row['relative_residual']}; wall={row['wall_seconds']} s", flush=True)
    return row


def report(results):
    rows = [json.loads(path.read_text()) for path in sorted(results.glob("[0-9]*-*.json"))]
    if not rows:
        raise ValueError(f"No recorded case results in {results}")
    fields = ("matrix_id", "matrix", "policy", "solver", "status", "iterations",
              "relative_residual", "relative_error", "setup_ms", "solve_ms", "total_ms",
              "assembly_ms", "wall_seconds", "exit_code", "log_sha256")
    with (results / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# Optional SuiteSparse results", "",
             "CPU Release, one MPI rank, one thread, manufactured `randsol` RHS and zero initial guess.",
             "PCG + AMG/FSAI; GMRES(50) + ILU. Tolerance 1e-8, at most 1,500 iterations.",
             "Exact YAML policies retain any matrix-specific AMG settings.",
             "These are individual measurements on the host in `environment.json`; repeat close timings.",
             "Input download and import are excluded from setup + solve. Matrix archives are fetched separately.",
             "Failures and timeouts are retained alongside successful solves.", "",
             "| Matrix / ID | Policy | Status | Iterations | Relative residual | Relative error | Setup + solve (ms) |",
             "|---|---|---|---:|---:|---:|---:|"]
    for row in rows:
        def number(key, fmt):
            return format(row[key], fmt) if row[key] is not None else "—"
        lines.append(f"| {row['matrix']} / {row['matrix_id']} | {row['policy']} | {row['status']} | "
                     f"{number('iterations', 'd')} | {number('relative_residual', '.2e')} | "
                     f"{number('relative_error', '.2e')} | {number('total_ms', '.3f')} |")
    lines += ["", "Raw outputs: `<ID>-<policy>.txt`; per-case records: `<ID>-<policy>.json`.",
              "`policies/` retains the exact YAML inputs and each JSON record includes input/policy/log SHA-256 checksums.",
              "Download URLs, Matrix Market checksums, dimensions and explicit-zero counts are in `lab/matrices.json`.",
              "Fault_639 and Emilia_923 contain explicit zeros; see lab/matrices.json for exact counts.",
              "", "From the workshop root, reproduce a case after setup:", "", "```bash",
              "python3 lab/suitesparse.py list", "python3 lab/suitesparse.py run 2547", "```",
              "", "Use `run all` to attempt the complete list. A nonzero exit means a retained failed solve or timeout.",
              "`report RESULTS_DIR` regenerates this table and CSV from the per-case JSON records.", ""]
    (results / "README.md").write_text("\n".join(lines))
    return rows


def print_summary(rows):
    columns = (("Matrix / ID", 28), ("Policy", 6), ("Status", 12), ("Iters", 6),
               ("Rel residual", 12), ("Rel error", 12), ("Setup ms", 10),
               ("Solve ms", 10), ("Sum ms", 10))

    def show(values):
        return "  ".join(value.ljust(width) if i < 3 else value.rjust(width)
                         for i, (value, (_, width)) in enumerate(zip(values, columns)))

    print("\nSummary:")
    print(show([name for name, _ in columns]))
    print(show(["-" * width for _, width in columns]))
    for row in rows:
        def number(key, spec):
            value = row.get(key)
            return "—" if value is None else format(value, spec)
        values = [f"{row['matrix']} / {row['matrix_id']}", row["policy"], row["status"],
                  number("iterations", "d"), number("relative_residual", ".2e"),
                  number("relative_error", ".2e"), number("setup_ms", ".3f"),
                  number("solve_ms", ".3f"), number("total_ms", ".3f")]
        print(show(values))


def run(args):
    work = workspace(args.work)
    cli = Path(args.cli or os.environ.get("CLI", str(work.parent / "build/hypredrive-cli"))).resolve()
    if not cli.is_file() or not os.access(cli, os.X_OK):
        raise ValueError("The hypredrive CLI is missing. Run setup and activate first.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = Path(args.results).expanduser().resolve() if args.results else work / "out/suitesparse" / stamp
    results.mkdir(parents=True, exist_ok=True)
    (results / "policies").mkdir(exist_ok=True)
    info = environment(args)
    previous = results / "environment.json"
    if previous.exists():
        old = json.loads(previous.read_text())
        keys = ("catalog_sha256", "source_pins", "policies", "timeout_seconds")
        if not args.resume or any(old[key] != info[key] for key in keys):
            raise ValueError("Results already exist. Use a new --results folder, or --resume with unchanged settings.")
    else:
        previous.write_text(json.dumps(info, indent=2) + "\n")
    print(f"Results: {results}", flush=True)
    attempted = []
    for matrix in select(args.matrix):
        fetch(matrix, work)
        for policy in POLICIES:
            record = results / f"{matrix['id']}-{policy}.json"
            if args.resume and record.is_file():
                row = json.loads(record.read_text())
                verify(record.with_suffix(".txt"), row["log_sha256"])
                verify(results / "policies" / record.with_suffix(".yml").name, row["policy_sha256"])
                print(f"Retaining {row['matrix']} / {policy}: {row['status']}", flush=True)
            else:
                row = run_case(matrix, policy, cli, work, results, args.timeout)
            attempted.append(row)
            report(results)
    print_summary(attempted)
    print(f"Saved raw logs, exact policies and summary: {results}", flush=True)
    return 0 if all(row["status"] == "converged" for row in attempted) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    fetcher = commands.add_parser("fetch")
    fetcher.add_argument("matrix")
    fetcher.add_argument("--work")
    runner = commands.add_parser("run")
    runner.add_argument("matrix")
    runner.add_argument("--work")
    runner.add_argument("--cli")
    runner.add_argument("--results")
    runner.add_argument("--resume", action="store_true")
    runner.add_argument("--timeout", type=float, default=600, help="seconds per policy (default: 600)")
    summary = commands.add_parser("report")
    summary.add_argument("results", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "list":
            for matrix in catalog():
                print(f"{matrix['id']:4d}  {matrix['group']}/{matrix['name']:15s}  "
                      f"{matrix['rows']:>9,d} rows  {matrix['nonzeros']:>11,d} nonzeros  "
                      f"{matrix['description']}")
        elif args.command == "fetch":
            for matrix in select(args.matrix):
                print(fetch(matrix, workspace(args.work)))
        elif args.command == "report":
            report(args.results.resolve())
        else:
            if not math.isfinite(args.timeout) or args.timeout <= 0:
                raise ValueError("Timeout must be a positive finite number.")
            return run(args)
    except (OSError, ValueError, KeyError, tarfile.TarError) as error:
        parser.exit(2, str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
