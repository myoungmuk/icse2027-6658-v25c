#!/usr/bin/env python3
"""Recompute the reviewer-item checks of paper Sections IV-C and IV-E from public files.

Inputs: t987_human_labels.csv and t987_reviewer_item_links.csv (this folder), plus the archived
hosted failing-patch control and the adapted-pilot verdicts already in this repository.
Standard library only; run from any directory. These are decision-level agreement rates with
unadjudicated non-maintainer majorities, not validation of individual rationale sentences.
"""
import csv, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
rows = {r["case_id"]: r for r in csv.DictReader(open(HERE / "t987_human_labels.csv", encoding="utf-8"))}
links = {r["case_id"]: r for r in csv.DictReader(open(HERE / "t987_reviewer_item_links.csv", encoding="utf-8"))}
assert set(rows) == set(links) and len(rows) == 987
H = {i: int(r["human_majority_merge"]) if r["human_majority_merge"] else None for i, r in rows.items()}


def cohen(pairs):
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    n = len(pairs)
    po = sum(x == y for x, y in pairs) / n
    pa, pb = sum(x for x, _ in pairs) / n, sum(y for _, y in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe), n


def split(pairs):
    """(LLM rejects, human also rejects, LLM accepts, human rejects among them) over labelled rows."""
    lab = [(l, h) for l, h in pairs if h is not None]
    return (sum(l == 0 for l, _ in lab), sum(l == 0 and h == 0 for l, h in lab),
            sum(l == 1 for l, _ in lab), sum(l == 1 and h == 0 for l, h in lab))


# Gold (developer) rejections, factorial Lite/Verified rows
dev = [i for i, r in rows.items() if r["patch_stratum"] == "developer" and r["factorial_7b_E1B1"] in ("0", "1")]
base = [H[i] for i in dev if H[i] is not None]
q7 = split([(int(rows[i]["factorial_7b_E1B1"]), H[i]) for i in dev])
hosted_gold = split([(int(rows[i]["hosted_claude_mergeable"]), H[i]) for i in rows
                     if rows[i]["patch_stratum"] == "developer" and rows[i]["hosted_claude_mergeable"] in ("0", "1")])
print(f"developer rows labelled {len(base)}, human reject {base.count(0)}; Qwen-7B E1B1 rejects {q7[0]}, humans also {q7[1]}; "
      f"hosted gold rejects {hosted_gold[0]}, humans also {hosted_gold[1]}")

# Hosted failing-patch control, mapped by identical diff (verified here against the archived packets)
pk_dir = REPO / "historical_analysis/data/review_packets/verified_negctrl"
cl_dir = REPO / "historical_analysis/data/llm_reviews/verified_negctrl/reviewer-claude-frontier"
diffs = {json.loads(l)["packet_id"]: json.loads(l)["diff"] for l in open(pk_dir / "packets.jsonl", encoding="utf-8")}
neg = []
for i, l in links.items():
    if l["hosted_negctrl_packet_id"]:
        d = diffs[l["hosted_negctrl_packet_id"]].replace("\r\n", "\n")
        assert hashlib.sha256(d.encode()).hexdigest() == l["hosted_negctrl_diff_sha256_lf"], i
        assert rows[i]["patch_stratum"] == "agent_unresolved", i
        v = json.load(open(cl_dir / f"{l['hosted_negctrl_packet_id']}.json", encoding="utf-8"))
        neg.append((1 if v.get("mergeable") else 0, H[i]))
k_neg, n_neg = cohen(neg)
hf = split(neg)
print(f"hosted failing control in T987 {len(neg)}, labelled {n_neg}: hosted rejects {hf[0]} (humans also {hf[1]}), "
      f"accepts {hf[2]} (humans reject {hf[3]}), kappa {k_neg:.3f}")

# Held-out follow-up tasks: strict vs adjusted
fu = {}
for g in ("followup_7b", "followup_14b", None):
    sel = [i for i, r in rows.items() if links[i]["followup_partition"] == "heldout" and (g is None or r["study_group"] == g)]
    for c in ("followup_strict", "followup_adjusted"):
        fu[(g, c)] = cohen([(H[i], int(rows[i][c])) for i in sel if rows[i][c] in ("0", "1")])
print("held-out follow-up kappa", {f"{g or 'pooled'} {c}": f"{k:.3f} (n={n})" for (g, c), (k, n) in fu.items()})

# Adapted prior-system follow-up pilot (Table "adapted"), overlapping cases
pv = {(v["task_code"], v["source"], v["arm"]): v for v in
      csv.DictReader(open(REPO / "binary_pilots/followup_v2/analysis_v2/verdicts.csv", encoding="utf-8"))}
pilot = {}
for arm in ("icse_test_blind", "cihan_binary_diff", "shi_draft_rubric"):
    pairs = [(1 if pv[(l["pilot_v2_task_code"], l["pilot_v2_source"], arm)]["decision"] == "ACCEPT" else 0, H[i])
             for i, l in links.items() if l["pilot_v2_task_code"]]
    pilot[arm] = cohen(pairs)
overlap = sum(1 for l in links.values() if l["pilot_v2_task_code"])
print(f"adapted pilot candidates in T987 {overlap}:", {a: f"{k:.3f} (n={n})" for a, (k, n) in pilot.items()})

assert (len(base), base.count(0)) == (408, 96) and q7[:2] == (288, 77) and hosted_gold[:2] == (3, 2)
assert (len(neg), n_neg) == (45, 39) and hf == (18, 18, 21, 17) and round(k_neg, 2) == 0.18
assert fu[(None, "followup_strict")][1] == 187 and round(fu[(None, "followup_strict")][0], 2) == 0.25
assert round(fu[(None, "followup_adjusted")][0], 2) == 0.15
assert [round(fu[(g, c)][0], 2) for g in ("followup_7b", "followup_14b") for c in ("followup_strict", "followup_adjusted")] == [0.23, 0.33, 0.24, -0.04]
assert overlap == 20 and [round(pilot[a][0], 2) for a in pilot] == [0.30, 0.21, 0.18]
print("all reviewer-item values reproduced")
