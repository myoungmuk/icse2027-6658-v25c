# ICSE 2027 #6658 · v25c

**Beyond %Resolved:Reassessing SWE-bench Through Human and LLM Code Review**

Myeongmuk Kang and Geunseok Yang

- [v25c manuscript PDF](icse2027-6658_v25c_artifact.pdf)
- [Matching LaTeX source ZIP](icse2027-6658_source_v25c_artifact.zip)
- [Pinned replication package](https://github.com/myoungmuk/icse2027-6658-v25c/tree/v25c-artifact)

## Research materials and reanalysis

| Materials | Where to find them |
| --- | --- |
| Original review packets, unadjusted and adjusted prompts, model verdicts, historical results and reanalysis instructions | [Historical analysis](historical_analysis/REPRODUCE.md) |
| Inputs, frozen prompts, outputs and analysis for the two-model, four-condition factorial experiment (9,624 planned and valid responses) | [Factorial protocol and offline reanalysis](factorial_v21/README.md) · [Raw evidence ZIP](factorial_v21/evidence/factorial_raw_evidence.zip) |
| Three raters’ pseudonymized verdicts over 987 issues, including the 841 common no-hold cases, and the code for Table XI and agreement checks | [Human-review data and reproduction](humanstudy_v24/human_study_t987/README.md) |
| Follow-up controls, paired and held-out results, binary-judge adaptations and technical or historical checks | [Follow-up](nonhuman_followup/README.md) · [Held-out calibration](task_disjoint_calibration/README.md) · [Binary pilots](binary_pilots/) · [Rationale audit](rationale_case_audit/README.md) · [History checks](postmerge_history/) |

Run these checks from the repository root with Python 3.

```sh
python3 tools/verify_manifest.py
python3 humanstudy_v24/human_study_t987/reproduce_t987.py
python3 humanstudy_v24/human_study_t987/reproduce_reviewer_items.py
```

The human-review script uses the same 841 cases without a hold for all pairwise Cohen’s κ comparisons, yielding 0.75–0.85 to two decimal places.
For the factorial analysis, unzip the evidence bundle and follow its offline instructions. Recorded responses support reanalysis. Exact replay of the hosted Claude inference is limited by missing execution metadata.

[Third-party rights notices](historical_analysis/THIRD_PARTY_NOTICES.md) apply to the upstream materials.
For provenance, the public data and scripts build on the [archived study package](https://github.com/myoungmuk/icse2027-6658-artifact-20261105-v2/tree/2026.11.24-v24); the versioned directories identify the individual experiments.
