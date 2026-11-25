#!/usr/bin/env python3
"""Recompute every T987 human-study number reported in the paper from t987_human_labels.csv.

Standard library only. Binary coding: merge=1, request_changes/reject=0, hold=excluded.
A human label is a majority of at least two concordant non-hold verdicts (no adjudication).
Run: python3 reproduce_t987.py  (prints the values and asserts the paper's rounded figures).
"""
import csv, math, random
from pathlib import Path

rows = list(csv.DictReader(open(Path(__file__).with_name("t987_human_labels.csv"), encoding="utf-8")))
assert len(rows) == 987
RK = ("R1", "R2", "R3")
BIN = {"merge": 1, "request_changes": 0, "reject": 0, "hold": None}
B = {rk: [BIN[r[f"{rk}_verdict"]] for r in rows] for rk in RK}
V = {rk: [r[f"{rk}_verdict"] for r in rows] for rk in RK}
S = [r["patch_stratum"] for r in rows]
N = range(len(rows))


def fleiss(items, cats):
    n, m = len(items), len(items[0])
    pj = [sum(it.count(c) for it in items) / (n * m) for c in cats]
    pi = [(sum(it.count(c) ** 2 for c in cats) - m) / (m * (m - 1)) for it in items]
    pe = sum(p * p for p in pj)
    return (sum(pi) / n - pe) / (1 - pe)


def cohen(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pairs)
    po = sum(x == y for x, y in pairs) / n
    pa, pb = sum(x for x, _ in pairs) / n, sum(y for _, y in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe), po, n


def fisher(a, b, c, d):
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    p = lambda x: math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)
    obs = p(a)
    return sum(p(x) for x in range(max(0, c1 - r2), min(r1, c1) + 1) if p(x) <= obs * (1 + 1e-9))


complete = [i for i in N if all(B[rk][i] is not None for rk in RK)]
items = [[B[rk][i] for rk in RK] for i in complete]
k_bin = fleiss(items, [0, 1])
rng = random.Random(20261123)
boot = sorted(fleiss([rng.choice(items) for _ in items], [0, 1]) for _ in range(2000))
ci = (boot[50], boot[1949])
k3 = fleiss([[V[rk][i] for rk in RK] for i in complete], ["merge", "request_changes", "reject"])
# Compute all rater pairs on the common non-hold set used in the manuscript.
pair = [
    cohen([B[a][i] for i in complete], [B[b][i] for i in complete])[0]
    for a, b in (("R1", "R2"), ("R1", "R3"), ("R2", "R3"))
]
unanimous = sum(len(set(it)) == 1 for it in items)
prespecified = sum(1 for i in complete if all(rows[i][f"{rk}_prior_awareness"] == "none" for rk in RK))


def majority(i):
    v = [B[rk][i] for rk in RK if B[rk][i] is not None]
    return 1 if v.count(1) >= 2 else 0 if v.count(0) >= 2 else None


H = [majority(i) for i in N]
assert [str(h) if h is not None else "" for h in H] == [r["human_majority_merge"] for r in rows]
acc = {}
for s in ("developer", "agent_resolved", "agent_unresolved"):
    v = [H[i] for i in N if S[i] == s and H[i] is not None]
    acc[s] = (sum(v), len(v))
f_dev_res = fisher(acc["developer"][0], acc["developer"][1] - acc["developer"][0],
                   acc["agent_resolved"][0], acc["agent_resolved"][1] - acc["agent_resolved"][0])
f_res_un = fisher(acc["agent_resolved"][0], acc["agent_resolved"][1] - acc["agent_resolved"][0],
                  acc["agent_unresolved"][0], acc["agent_unresolved"][1] - acc["agent_unresolved"][0])

print(f"no-hold cases {len(complete)}, prespecified agreement set {prespecified}, undetermined {H.count(None)}")
print(f"Fleiss binary {k_bin:.3f} CI {ci[0]:.3f}-{ci[1]:.3f}; 3-category {k3:.3f}; pairwise {[round(k, 3) for k in pair]}; unanimous {unanimous}")
print("majority acceptance", {s: f"{a}/{n} ({100 * a / n:.1f}%)" for s, (a, n) in acc.items()})
print(f"Fisher developer vs resolved p={f_dev_res:.3g}; resolved vs unresolved p={f_res_un:.3g}")

llm = {}
for col in [c for c in rows[0] if c.startswith("factorial_")] + ["followup_strict", "followup_adjusted", "hosted_claude_mergeable"]:
    src = [int(r[col]) if r[col] in ("0", "1") else None for r in rows]
    k, po, n = cohen(H, src)
    llm[col] = k
    cells = []
    for s in ("developer", "agent_resolved", "agent_unresolved"):
        sel = [i for i in N if S[i] == s and H[i] is not None and src[i] is not None]
        if sel:
            cells.append(f"{s} {100 * sum(src[i] for i in sel) / len(sel):.1f}/{100 * sum(H[i] for i in sel) / len(sel):.1f}")
    print(f"{col}: n={n} kappa={k:.3f} agreement={100 * po:.2f}% | LLM/human % " + "; ".join(cells))
shown = [int(r["displayed_ai_flag"]) for r in rows]
anchor = [cohen(B[rk], shown)[0] for rk in RK]
print("rater vs displayed AI flag kappa", [round(k, 3) for k in anchor])

assert len(complete) == 841 and prespecified == 0 and H.count(None) == 62 and unanimous == 724
assert round(k_bin, 2) == 0.81 and (round(ci[0], 2), round(ci[1], 2)) == (0.78, 0.84) and round(k3, 2) == 0.63
assert (round(min(pair), 2), round(max(pair), 2)) == (0.75, 0.85)
assert acc == {"developer": (399, 530), "agent_resolved": (81, 111), "agent_unresolved": (35, 284)}
assert round(f_dev_res, 2) == 0.63 and f_res_un < 1e-30
assert round(llm["hosted_claude_mergeable"], 2) == 0.34 and max(llm.values()) < 0.35
assert all(0.01 <= round(llm[f"factorial_14b_{c}"], 2) <= 0.04 for c in ("E0B0", "E1B0", "E0B1", "E1B1"))
assert all(0.07 <= round(llm[f"factorial_7b_{c}"], 2) <= 0.11 for c in ("E0B0", "E1B0", "E0B1", "E1B1"))
assert (round(min(anchor), 2), round(max(anchor), 2)) == (-0.03, -0.01)
print("all paper values reproduced")
