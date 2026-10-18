"""
SMPC fraud scoring with MPyC.  Run with ONE PROCESS PER BANK:
    python smpc/smpc_score.py -M3          # 3 banks
    python smpc/smpc_score.py -M5          # 5 banks
Number of banks = number of MPyC parties (-M).
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mpyc.runtime import mpc
from config import W, T_PER_BANK, DEFAULT_SEED
from data.generate_data import generate_data

secint = mpc.SecInt(32)   # 32-bit secure integers (max score 7*1150 = 8050, plenty)


async def _smpc(data, w, t_per_bank, mode):
    m = len(mpc.parties)
    assert len(data) == m, f"data has {m} banks' worth? need -M{len(data)}"
    pid = mpc.pid
    n_txn = len(data[pid])

    # ---- PROTECTION: this bank secret-shares ONLY ITS OWN records ----
    mine = [secint(v) for rec in data[pid] for v in rec]       # flat: f,a,b,f,a,b,...
    shared = mpc.input(mine, senders=list(range(m)))           # shared[bank][3*txn + field]
    # (other banks' real values never exist on this process; only shares do)

    # ---- COMPUTATION: weighted sum is LOCAL (weights are public constants) ----
    scores = []
    for j in range(n_txn):
        s = 0
        for b in range(m):
            f, a, bl = shared[b][3*j: 3*j + 3]
            s = s + w[0]*f + w[1]*a + w[2]*bl
        scores.append(s)

    if mode == "sum":                       # experiment: sum only, no comparison
        return await mpc.output(scores)

    # ---- COMPUTATION: secure comparison (the expensive step) ----
    threshold = t_per_bank * m
    verdicts = [s >= threshold for s in scores]

    # ---- RECONSTRUCTION: only the 0/1 verdicts are opened ----
    return [int(v) for v in await mpc.output(verdicts)]


def smpc_score(data, w=W, t_per_bank=T_PER_BANK, mode="verdict"):
    """returns verdicts only (list of 0/1); scores are never revealed.
    mode='sum' reveals the scores (weaker privacy, used for experiments only)."""
    async def run():
        await mpc.start()                       # connect the parties
        out = await _smpc(data, w, t_per_bank, mode)
        await mpc.shutdown()
        return out
    return mpc.run(run())


if __name__ == "__main__":
    m = len(mpc.parties)
    if m < 3:
        print("Need at least 3 banks. Run: python smpc/smpc_score.py -M3")
        sys.exit(1)
    n_txn = int(os.environ.get("TXNS", 20))
    data = generate_data(m, n_txn, DEFAULT_SEED)     # simulation: every process builds all data,
                                                      # but only data[mpc.pid] is ever input.
    t0 = time.perf_counter()
    verdicts = smpc_score(data)
    ms = (time.perf_counter() - t0) * 1000

    # ---- VERIFICATION vs plaintext (quick self-check; B owns the full one) ----
    plain = [int(sum(W[0]*data[b][j][0] + W[1]*data[b][j][1] + W[2]*data[b][j][2]
                     for b in range(m)) >= T_PER_BANK * m) for j in range(n_txn)]
    if mpc.pid == 0:
        print(f"banks={m} txns={n_txn} time={ms:.1f} ms")
        print("verdicts :", verdicts)
        print("plaintext:", plain)
        print("MATCH" if verdicts == plain else "MISMATCH", f"| flagged {sum(verdicts)}/{n_txn}")