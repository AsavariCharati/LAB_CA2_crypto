"""Sanity checks for config + data generator. Run from repo root: python check_data.py"""
from config import W, T_PER_BANK, FLAGS_RANGE, AMOUNT_RANGE
from data.generate_data import generate_data

ok = True
def check(name, cond):
    global ok
    print(("PASS  " if cond else "FAIL  ") + name)
    ok = ok and cond

for banks in (3, 5, 7):
    d = generate_data(banks, 200, 42)
    check(f"{banks} banks: right shape", len(d) == banks and all(len(b) == 200 for b in d))
    recs = [r for b in d for r in b]
    check(f"{banks} banks: flags in {FLAGS_RANGE}", all(FLAGS_RANGE[0] <= r[0] <= FLAGS_RANGE[1] for r in recs))
    check(f"{banks} banks: amount in {AMOUNT_RANGE}", all(AMOUNT_RANGE[0] <= r[1] <= AMOUNT_RANGE[1] for r in recs))
    check(f"{banks} banks: blacklist is 0/1", all(r[2] in (0, 1) for r in recs))
    check(f"{banks} banks: all integers", all(isinstance(v, int) for r in recs for v in r))
    scores = [sum(W[0]*d[b][j][0] + W[1]*d[b][j][1] + W[2]*d[b][j][2] for b in range(banks)) for j in range(200)]
    flagged = sum(s >= T_PER_BANK * banks for s in scores)
    check(f"{banks} banks: some but not all flagged ({flagged}/200)", 0 < flagged < 100)

check("same seed gives same data", generate_data(3, 50, 42) == generate_data(3, 50, 42))
check("different seed gives different data", generate_data(3, 50, 42) != generate_data(3, 50, 7))
print("\nALL PASSED" if ok else "\nSOMETHING FAILED")