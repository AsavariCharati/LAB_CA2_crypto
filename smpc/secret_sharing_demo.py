"""
Hand-written additive secret sharing (no library).
Shows the concept BEFORE we use MPyC, so we can explain it in the viva.
"""
import random

P = 2**31 - 1   # public prime modulus, all arithmetic is mod P

def share(secret, n):
    """Split secret into n random shares that add up to secret (mod P)."""
    shares = [random.randrange(P) for _ in range(n - 1)]
    shares.append((secret - sum(shares)) % P)
    return shares

def reconstruct(shares):
    return sum(shares) % P

if __name__ == "__main__":
    random.seed(1)
    inputs = {"Bank A": 40, "Bank B": 70, "Bank C": 90}   # the doc's own example
    names = list(inputs)
    n = len(names)

    # 1. PROTECTION: every bank splits its secret and gives one share to each bank
    all_shares = {name: share(v, n) for name, v in inputs.items()}
    print("--- Step 1: each bank splits its secret ---")
    for name, s in all_shares.items():
        print(f"{name} secret={inputs[name]:>3} -> shares {s}")

    # 2. COMPUTATION: each bank adds up the shares IT received (one from every bank)
    local_sums = []
    print("\n--- Step 2: each bank adds the shares it received ---")
    for i, name in enumerate(names):
        received = [all_shares[src][i] for src in names]
        local_sums.append(sum(received) % P)
        print(f"{name} holds {received} -> local sum {local_sums[-1]}")

    # 3. RECONSTRUCTION: only the sums of shares are combined
    total = reconstruct(local_sums)
    print(f"\n--- Step 3: combined result = {total} (expected {sum(inputs.values())}) ---")
    assert total == sum(inputs.values())

    # 4. PRIVACY: what does ONE bank see of Bank A's secret? random noise
    print("\n--- Privacy check ---")
    print("Bank B sees only one share of Bank A's input:", all_shares["Bank A"][1],
          "(looks random, tells nothing about 40)")

    # 5. COLLUSION: all n shares are needed; n-1 reveal nothing, but n reveal everything
    leaked = reconstruct(all_shares["Bank A"])
    print(f"Banks A+B+C colluding recover Bank A's input: {leaked}")
    missing_one = (sum(all_shares['Bank A'][:-1])) % P
    print(f"Any {n-1} shares alone give {missing_one} (meaningless without the last share)")