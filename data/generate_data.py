import numpy as np
from config import (
    FLAGS_RANGE,
    AMOUNT_RANGE,
    FRAUD_RATE,
    DEFAULT_SEED,
    W,
    T_PER_BANK,
)


def generate_data(num_banks, num_txns, seed=DEFAULT_SEED):
    """
    Generates synthetic multi-bank transaction data.
    
    Returns:
        data[bank][txn] = (flags, amount, blacklist)
        where all values are plain Python int.
    """
    rng = np.random.default_rng(seed)
    data = [[] for _ in range(num_banks)]

    min_flag, max_flag = FLAGS_RANGE
    min_amt, max_amt = AMOUNT_RANGE

    for _ in range(num_txns):
        is_fraud = bool(rng.random() < FRAUD_RATE)
        # In a fraudulent case, at least one bank has already flagged or blacklisted
        bl_bank = int(rng.integers(0, num_banks))

        for b in range(num_banks):
            if is_fraud:
                # Fraudulent patterns: elevated flags, higher amounts, blacklist presence
                f_val = int(rng.integers(8, max_flag + 1))
                a_val = int(rng.integers(int(max_amt * 0.4), max_amt + 1))
                bl_val = 1 if (b == bl_bank or rng.random() < 0.35) else 0
            else:
                # Legitimate patterns: low flags, regular amounts, rare false-positive blacklist
                f_val = int(rng.integers(min_flag, min(min_flag + 4, max_flag + 1)))
                a_val = int(rng.integers(min_amt, min(min_amt + 151, max_amt + 1)))
                bl_val = 1 if rng.random() < 0.015 else 0

            # Ensure bounds and plain Python int
            f_val = int(max(min_flag, min(max_flag, f_val)))
            a_val = int(max(min_amt, min(max_amt, a_val)))
            bl_val = int(bl_val)

            data[b].append((f_val, a_val, bl_val))

    return data