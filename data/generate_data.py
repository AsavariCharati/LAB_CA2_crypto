import random
from config import DEFAULT_SEED, FRAUD_RATE

def generate_data(num_banks, num_txns, seed=DEFAULT_SEED):
    """returns data[bank][txn] = (flags, amount, blacklist)"""
    rng = random.Random(seed)
    data = [[] for _ in range(num_banks)]
    for _ in range(num_txns):
        fraud = rng.random() < FRAUD_RATE
        # at least one bank blacklists a fraudulent customer
        bl_bank = rng.randrange(num_banks)
        for b in range(num_banks):
            if fraud:
                flags = rng.randint(8, 20)
                amount = rng.randint(400, 1000)
                bl = 1 if (b == bl_bank or rng.random() < 0.3) else 0
            else:
                flags = rng.randint(0, 3)
                amount = rng.randint(0, 150)
                bl = 1 if rng.random() < 0.02 else 0
            data[b].append((flags, amount, bl))
    return data