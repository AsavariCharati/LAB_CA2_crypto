# config.py  (shared by everyone, do not edit without telling the team)

W = (5, 1, 50)            # weights for (flags, amount, blacklist)
T_PER_BANK = 300          # threshold per bank, total = T_PER_BANK * num_banks
FLAGS_RANGE = (0, 20)
AMOUNT_RANGE = (0, 1000)  # in thousands
FRAUD_RATE = 0.10
DEFAULT_SEED = 42

# data[bank][txn] = (flags, amount, blacklist)
# Index txn i refers to the SAME customer/transaction across all banks.
# function contracts

def generate_data(num_banks, num_txns, seed=DEFAULT_SEED):
    """returns data[bank][txn] = (flags, amount, blacklist)"""

def conventional_score(data, w=W, t_per_bank=T_PER_BANK):
    """returns (scores, verdicts); verdict 1 = suspicious"""

def smpc_score(data, w=W, t_per_bank=T_PER_BANK):
    """returns verdicts only (list of 0/1), scores are never revealed"""