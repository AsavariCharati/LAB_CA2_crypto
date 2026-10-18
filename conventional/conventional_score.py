"""
Conventional (centralized / cleartext) fraud scoring baseline.
All banks pool raw transaction records into a single central database/server.
Computes weighted fraud scores and binary verdicts without privacy protection.
"""
import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import W, T_PER_BANK, DEFAULT_SEED
from data.generate_data import generate_data


def conventional_score(data, w=W, t_per_bank=T_PER_BANK):
    """
    Computes centralized fraud scores and verdicts across all banks.

    Args:
        data: data[bank][txn] = (flags, amount, blacklist)
        w: tuple of weights (flags_weight, amount_weight, blacklist_weight)
        t_per_bank: per-bank threshold; total threshold = t_per_bank * num_banks

    Returns:
        (scores, verdicts):
            scores: list of integer fraud scores per transaction
            verdicts: list of 0 or 1 (1 = suspicious / flagged)
    """
    num_banks = len(data)
    if num_banks == 0:
        return [], []

    num_txns = len(data[0])
    threshold = t_per_bank * num_banks

    scores = []
    verdicts = []

    for j in range(num_txns):
        # Centralized server aggregates raw inputs from every bank
        txn_score = 0
        for b in range(num_banks):
            flags, amount, bl = data[b][j]
            txn_score += w[0] * flags + w[1] * amount + w[2] * bl

        scores.append(int(txn_score))
        verdicts.append(1 if txn_score >= threshold else 0)

    return scores, verdicts


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Conventional Centralized Fraud Scoring Baseline")
    parser.add_argument("-b", "--banks", type=int, default=3, help="Number of banks (default: 3)")
    parser.add_argument("-t", "--txns", type=int, default=20, help="Number of transactions (default: 20)")
    parser.add_argument("-s", "--seed", type=int, default=DEFAULT_SEED, help="Random seed (default: 42)")
    args = parser.parse_args()

    data = generate_data(args.banks, args.txns, seed=args.seed)

    t0 = time.perf_counter()
    scores, verdicts = conventional_score(data)
    ms = (time.perf_counter() - t0) * 1000

    flagged_count = sum(verdicts)
    print(f"[Conventional Score] banks={args.banks} txns={args.txns} time={ms:.3f} ms")
    print(f"Threshold: {T_PER_BANK * args.banks} (T_PER_BANK={T_PER_BANK})")
    print(f"Scores   : {scores}")
    print(f"Verdicts : {verdicts}")
    print(f"Flagged  : {flagged_count}/{args.txns} ({flagged_count / args.txns * 100:.1f}%)")
