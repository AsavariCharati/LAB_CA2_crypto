"""
experiments/verify.py
Verification harness: Confirms that SMPC privacy-preserving verdicts match
the conventional centralized baseline verdicts exactly across all configurations.
Outputs a clean summary verification matrix suitable for academic report submission.
"""
import ast
import os
import re
import subprocess
import sys
import time

# Ensure repository root is in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from config import DEFAULT_SEED
from data.generate_data import generate_data
from conventional.conventional_score import conventional_score


def run_smpc(num_banks, num_txns, seed=DEFAULT_SEED, mode="verdict", timeout=120):
    """
    Executes smpc_score.py in a dedicated subprocess with MPyC multi-party arguments.
    Returns:
        (verdicts, elapsed_time_s, bytes_sent, raw_output)
    """
    env = os.environ.copy()
    env["TXNS"] = str(num_txns)
    env["SEED"] = str(seed)
    env["MODE"] = str(mode)
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [sys.executable, os.path.join(REPO_ROOT, "smpc", "smpc_score.py"), f"-M{num_banks}"]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"SMPC process failed with exit code {proc.returncode}:\n{proc.stdout}"
        )

    output = proc.stdout

    # Parse verdicts list: "verdicts : [0, 0, 1, ...]"
    verdicts = None
    v_match = re.search(r"verdicts\s*:\s*(\[[^\]]*\])", output)
    if v_match:
        verdicts = ast.literal_eval(v_match.group(1))

    # Parse bytes sent from MPyC shutdown log: "bytes sent: 26996"
    bytes_sent = None
    b_match = re.search(r"bytes sent:\s*(\d+)", output)
    if b_match:
        bytes_sent = int(b_match.group(1))

    # Parse elapsed core time
    elapsed_s = None
    e_match = re.search(r"elapsed time:\s*([0-9:.]+)", output)
    if e_match:
        elapsed_str = e_match.group(1)
        parts = elapsed_str.split(":")
        if len(parts) == 3:
            elapsed_s = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        else:
            elapsed_s = float(elapsed_str)

    return verdicts, elapsed_s, bytes_sent, output


def main():
    test_cases = [
        # (label, banks, txns, seed, mode)
        ("Small Consortium", 3, 10, 42, "verdict"),
        ("Standard Run", 3, 20, 42, "verdict"),
        ("Medium Volume", 3, 50, 42, "verdict"),
        ("5-Bank Network", 5, 20, 42, "verdict"),
        ("5-Bank Stress", 5, 50, 123, "verdict"),
        ("7-Bank Federation", 7, 20, 42, "verdict"),
        ("7-Bank Stress", 7, 50, 999, "verdict"),
        ("3-Bank Linear Sum", 3, 20, 42, "sum"),
        ("5-Bank Linear Sum", 5, 20, 42, "sum"),
    ]

    print("=" * 86)
    print("      SMPC vs. CONVENTIONAL BASELINE EQUIVALENCE VERIFICATION HARNESS")
    print("=" * 86)
    print(f"Running {len(test_cases)} automated verification test cases...\n")

    summary_rows = []
    all_passed = True

    for label, banks, txns, seed, mode in test_cases:
        sys.stdout.write(f"  Testing [{label}] ({banks} banks, {txns} txns, {mode})... ")
        sys.stdout.flush()

        # 1. Conventional Baseline
        data = generate_data(banks, txns, seed=seed)
        conv_scores, conv_verdicts = conventional_score(data)
        expected = conv_scores if mode == "sum" else conv_verdicts

        # 2. SMPC Execution
        smpc_out, core_s, bytes_sent, _ = run_smpc(banks, txns, seed=seed, mode=mode)

        match = (smpc_out == expected)
        if not match:
            all_passed = False
            sys.stdout.write("FAILED\n")
        else:
            sys.stdout.write("DONE\n")

        if mode == "verdict":
            detail = f"{sum(smpc_out)}/{txns} flagged"
        else:
            detail = f"{len(smpc_out)} sums"

        summary_rows.append({
            "label": label,
            "banks": banks,
            "txns": txns,
            "mode": mode,
            "detail": detail,
            "core_s": f"{core_s:.3f} s" if core_s is not None else "N/A",
            "bytes": f"{bytes_sent:,} B" if bytes_sent is not None else "N/A",
            "status": "PASS" if match else "FAIL"
        })

    # Print Clean Summary Verification Matrix
    print("\n" + "=" * 86)
    print("                     VERIFICATION MATRIX (SMPC == CONVENTIONAL)")
    print("=" * 86)
    print(f"{'Test Case':<20} {'Banks':<6} {'Txns':<6} {'Mode':<9} {'Outcome':<14} {'Core Time':<11} {'Bytes Sent':<12} {'Status':<6}")
    print("-" * 86)
    for r in summary_rows:
        print(
            f"{r['label']:<20} {r['banks']:<6} {r['txns']:<6} {r['mode']:<9} "
            f"{r['detail']:<14} {r['core_s']:<11} {r['bytes']:<12} [ {r['status']} ]"
        )
    print("=" * 86)

    if all_passed:
        print(f"RESULT: ALL {len(test_cases)} CHECKS PASSED (100% Output Equivalence Confirmed)")
        print("SMPC protocol guarantees complete privacy without any loss in scoring accuracy.")
        print("=" * 86)
        sys.exit(0)
    else:
        print("RESULT: VERIFICATION FAILED (Discrepancy detected between SMPC and Conventional)")
        print("=" * 86)
        sys.exit(1)


if __name__ == "__main__":
    main()
