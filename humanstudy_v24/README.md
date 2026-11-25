# ICSE #6658 v24: three-rater human review

- The [current manuscript](../icse2027-6658_v25c_artifact.pdf) describes the human review in Section IV-E.
- `human_study_t987/`: pseudonymized verdicts of three non-author graduate-student raters
  on 987 unique issues (one patch each), archived LLM verdicts on the same patches, and
  `reproduce_t987.py`, which recomputes every reported human-study number with the Python
  standard library. Rater identities and free-text rationales are withheld.
- `technical_checks/`: the Django dbshell parser probe cited in Section IV-D and the Git
  commit times of archived hosted-reviewer verdicts cited in Section III. The probe script
  expects the preserved regression-audit source trees; paths are relative to the authors'
  workspace and need adaptation.

Run from any directory:

    python3 humanstudy_v24/human_study_t987/reproduce_t987.py
    python3 humanstudy_v24/human_study_t987/reproduce_reviewer_items.py

The second script recomputes the reviewer-item checks in Sections IV-C, IV-D and IV-E (human
corroboration of gold and failing-patch rejections, held-out follow-up agreement, adapted-pilot
agreement) from the human labels and the archived verdicts already in this repository.

Human labels are unadjudicated majorities of non-maintainer raters, not mergeability ground
truth. Protocol deviations are listed in `human_study_t987/README.md`. All earlier paths,
releases and historical limitations are preserved unchanged.
