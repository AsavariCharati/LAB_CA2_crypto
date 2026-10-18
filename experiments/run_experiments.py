"""
experiments/run_experiments.py
Runs empirical benchmarks comparing Centralized Conventional vs SMPC scoring.

Executes experiments across:
1. Scaling number of banks: 3, 5, 7 banks (fixed 100 txns)
2. Scaling transaction volume: 10, 100, 500 txns (fixed 3 banks)
3. Operation complexity: Secure Sum vs Full Secure Comparison (verdict) (100 txns across 3 & 5 banks)
4. Multi-party high-volume: 5 and 7 banks (100 and 500 txns)

Outputs benchmarks to `results.csv`.
"""
import ast
import csv
import os
import re
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from config import DEFAULT_SEED
from data.generate_data import generate_data
from conventional.conventional_score import conventional_score


def run_smpc_process(num_banks, num_txns, seed=DEFAULT_SEED, mode="verdict", timeout=180):
    """
    Spawns an independent process for smpc_score.py.
    Returns:
        (verdicts, wall_time_ms, core_time_s, bytes_sent, match_str)
    """
    env = os.environ.copy()
    env["TXNS"] = str(num_txns)
    env["SEED"] = str(seed)
    env["MODE"] = str(mode)
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [sys.executable, os.path.join(REPO_ROOT, "smpc", "smpc_score.py"), f"-M{num_banks}"]

    t_start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    wall_time_ms = (time.perf_counter() - t_start) * 1000

    if proc.returncode != 0:
        raise RuntimeError(
            f"SMPC process failed (exit code {proc.returncode}):\n{proc.stdout}"
        )

    output = proc.stdout

    # Parse verdicts
    verdicts = None
    v_match = re.search(r"verdicts\s*:\s*(\[[^\]]*\])", output)
    if v_match:
        verdicts = ast.literal_eval(v_match.group(1))

    # Parse core elapsed time and bytes sent
    bytes_sent = None
    b_match = re.search(r"bytes sent:\s*(\d+)", output)
    if b_match:
        bytes_sent = int(b_match.group(1))

    core_time_s = None
    e_match = re.search(r"elapsed time:\s*([0-9:.]+)", output)
    if e_match:
        elapsed_str = e_match.group(1)
        # Parse HH:MM:SS.fff into float seconds
        parts = elapsed_str.split(":")
        if len(parts) == 3:
            core_time_s = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        else:
            core_time_s = float(elapsed_str)

    match_str = "MATCH" in output

    return verdicts, wall_time_ms, core_time_s, bytes_sent, match_str


def run_benchmark(experiment_name, num_banks, num_txns, mode="verdict", seed=DEFAULT_SEED):
    print(f"\n[RUNNING] {experiment_name}: banks={num_banks}, txns={num_txns}, mode={mode}")

    # Benchmark conventional scoring
    data = generate_data(num_banks, num_txns, seed=seed)
    t0 = time.perf_counter()
    conv_scores, conv_verdicts = conventional_score(data)
    conv_time_ms = (time.perf_counter() - t0) * 1000

    expected_output = conv_scores if mode == "sum" else conv_verdicts

    # Benchmark SMPC scoring
    smpc_out, smpc_wall_ms, smpc_core_s, bytes_sent, _ = run_smpc_process(
        num_banks, num_txns, seed=seed, mode=mode
    )

    matches = (smpc_out == expected_output)
    flagged = sum(smpc_out) if mode == "verdict" else 0

    print(
        f"  Conv: {conv_time_ms:.3f} ms | SMPC Wall: {smpc_wall_ms:.1f} ms | "
        f"MPyC Core: {smpc_core_s:.3f} s | Bytes: {bytes_sent:,} | Match: {matches}"
    )

    return {
        "experiment": experiment_name,
        "num_banks": num_banks,
        "num_txns": num_txns,
        "mode": mode,
        "conventional_time_ms": round(conv_time_ms, 3),
        "smpc_time_ms": round(smpc_wall_ms, 1),
        "smpc_core_time_s": round(smpc_core_s, 4) if smpc_core_s is not None else None,
        "smpc_bytes_sent": bytes_sent,
        "flagged_count": flagged,
        "match": matches,
    }


def main():
    print("=" * 80)
    print("RUNNING PRIVACY-PRESERVING FRAUD DETECTION EXPERIMENTAL SUITE")
    print("=" * 80)

    results = []

    # Experiment 1: Scaling Banks (3, 5, 7 banks with 100 transactions)
    for b in (3, 5, 7):
        row = run_benchmark("varying_banks", num_banks=b, num_txns=100, mode="verdict")
        results.append(row)

    # Experiment 2: Scaling Transactions (10, 100, 500 transactions with 3 banks)
    for t in (10, 100, 500):
        # 100 txns already measured in exp 1, but we run or include for completeness
        row = run_benchmark("varying_txns", num_banks=3, num_txns=t, mode="verdict")
        results.append(row)

    # Experiment 3: Operation Overhead - Sum only vs Full Verdict scoring
    for b in (3, 5):
        row_sum = run_benchmark("sum_vs_verdict", num_banks=b, num_txns=100, mode="sum")
        results.append(row_sum)
        row_verdict = run_benchmark("sum_vs_verdict", num_banks=b, num_txns=100, mode="verdict")
        results.append(row_verdict)

    # Experiment 4: Multi-Party High-Volume Scaling (5 and 7 banks with 500 txns)
    for b in (5, 7):
        row = run_benchmark("multibank_volume", num_banks=b, num_txns=500, mode="verdict")
        results.append(row)

    # Write results to results.csv in both LAB_CA2_crypto and workspace root for convenience
    csv_paths = [
        os.path.join(REPO_ROOT, "results.csv"),
        os.path.join(os.path.dirname(REPO_ROOT), "results.csv"),
    ]

    fieldnames = [
        "experiment",
        "num_banks",
        "num_txns",
        "mode",
        "conventional_time_ms",
        "smpc_time_ms",
        "smpc_core_time_s",
        "smpc_bytes_sent",
        "flagged_count",
        "match",
    ]

    for path in csv_paths:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n[Saved Results] -> {path}")

    # Print summary table
    print("\n" + "=" * 90)
    print(f"{'Experiment':<18} {'Banks':<6} {'Txns':<6} {'Mode':<8} {'Conv (ms)':<10} {'SMPC (ms)':<10} {'MPyC (s)':<10} {'Bytes Sent':<12} {'Match':<6}")
    print("-" * 90)
    for r in results:
        bytes_str = f"{r['smpc_bytes_sent']:,}"
        print(
            f"{r['experiment']:<18} {r['num_banks']:<6} {r['num_txns']:<6} {r['mode']:<8} "
            f"{r['conventional_time_ms']:<10.3f} {r['smpc_time_ms']:<10.1f} {r['smpc_core_time_s']:<10.3f} "
            f"{bytes_str:<12} {str(r['match']):<6}"
        )
    print("=" * 90)


if __name__ == "__main__":
    main()
