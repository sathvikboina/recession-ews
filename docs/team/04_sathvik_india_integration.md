# Lane Brief 4 — India Coverage, Scope, Integration and Pitch

**Owner:** Sathvik Boina
**Role:** Validation, integration and writing lead
**Lane:** Part 4 of the one-week sprint
**Dates:** Days 1–5 individual; Days 6–7 shared merge and review
**Branch:** `feat/india-scope-docs`

> **Status 2026-11-13:** this lane has been executed as far as the available data allows.
> India's downloaded-data count is **1 of 8** (`ACT_IP` only), so O-2 stays Label-B-only.
> The Day 3 audit, Day 4 checklist, Day 5 pitch and integration checklist are in
> `04a_docs_audit.md` to `04e_part4_handoff.md`. Arshiya's clean-clone evidence, the other
> three lane branches and all model results remain pending.

---

## 1. Your mission in one paragraph

Close the India question with downloaded data or a recorded access failure, keep the
project's scope and claim wording honest, and **coordinate** the Day 6 merge and Day 7
go/no-go. You are the integration owner, not the owner of every check: Arshiya runs the
combined clean clone, Palchhin owns the results docs, Shravani owns the label docs, and each
lane owner merges their own branch. Your job is to make the pieces fit, write the
plain-English story, and stop the project from overclaiming.

## 2. What has already happened (so you do not repeat it)

- **The USA label is frozen as `labels-v3`.** 1990Q1–2026Q3 (147 quarters), 4/4 NBER
  recessions, zero false episodes, accuracy 0.993, precision 0.929, recall 1.000, F1 0.963.
  `labels-v1` and `labels-v2` are archived byte-identically.
- **The 2026 extension is done and verified.** The panel and reporting window moved from
  2025Q4 to 2026Q3 without changing the estimator, BBQ, diffusion gate or eight-indicator
  structure.
- **India is already pre-audited.** The best case is **4/8** core indicators, so under O-2
  India stays **Label-B-only**. The 6-of-8 rule is not relaxed. This lane exists to replace
  the pre-audit with actual download evidence, or to record why access failed.
- **The ensemble is pre-registered.** Equal-weight top-3 by inner-fold pooled PR-AUC, a
  ≥0.01 absolute gain, a bootstrap CI excluding zero, and no episode-recall loss. It is
  applied once. A negative result is reported.
- **The first model result is USA-first.** Japan and Germany join only if their labels pass
  and time allows. Do not delay the USA headline for a country label.
- **The whole-repository review is complete.** 38 tests pass; `make check` gives 33 ok,
  3 warnings (optional model packages), 0 failures; `build.py` reproduces all 13 root CSVs
  byte-for-byte; workbook cell diff is 0; frozen hashes unchanged. A fresh clone shows 36
  passed and 2 explicit skips until the git-ignored `data/clean` is rebuilt.
- **No feature table, folds, model or out-of-sample score exists yet.** That is what Parts
  2 and 3 build during the week.
- **Nothing is packaged, mirrored, zipped or tagged.** Day 7 packaging requires explicit
  approval; the default is to write findings instead.

**Read first:** `docs/TEAM_PLAN.md`, `docs/STATE.md`, `docs/BUILD_CONTRACT.md`,
`docs/PROPOSAL_ADDENDUM.md`, `docs/INDIA_COVERAGE_AUDIT.md`, `docs/DECISIONS.md`,
`docs/VERIFICATION.md`, `README.md`.

## 3. What you own: Days 1–5

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Download the candidate MoSPI/RBI India series, or record the exact access failure | `data/india_core_coverage.csv` | Every India core row has a downloaded-data status or a recorded failure; no proxy substituted |
| 2 | Close the India verdict: confirm the business/non-residential GFCF split and the official retail series; recompute 6/8 | Final India count and note | Count recorded (or access failure); O-2 stays Label-B-only; pre-audit 4/8 stays provisional if downloads fail |
| 3 | Audit the 2026 extension and sync docs **with Shravani and Palchhin** | Updated `README.md`, `docs/STATE.md`, `docs/VERIFICATION.md`, claim wording | Docs agree with `labels-v3`; no unsupported forecast claim; label docs and results docs cross-checked |
| 4 | Review Arshiya's dry-run clean clone of current `main` and the packaging checklist | Review note and checklist | Current `main` passes; nothing packaged or tagged; the combined clean clone is explicitly Day 7 |
| 5 | Run the integration rehearsal with all four and write the plain-English pitch | Rehearsal notes, one-page pitch | Merge order works; pitch says what the label proves and what the model result does not prove |

### Suggested daily rhythm

- **09:30 — 15-minute stand-up.** You facilitate, but each owner reports their own work.
- **Keep a decisions log.** If the team changes a rule before results, record the date and
  the reason; after results, do not rewrite history.
- **17:30 — integration note.** What merged cleanly, what is still open, and who owns it.
- **Day 6:** coordinate the merge in the fixed order; each owner merges their own branch.
  **Day 7:** coordinate cross-review and the go/no-go with Arshiya.

## 4. What we expect by Day 5

A complete Part 4 hand-off contains:

1. **India coverage table.** `data/india_core_coverage.csv` with a real status for every
   core row: downloaded, access-blocked, or not published. No proxy and no guess.
2. **India verdict.** Final 6/8 count or a recorded access failure; O-2 stays Label-B-only;
   the pre-audit 4/8 remains labelled provisional if downloads fail.
3. **Consistent docs.** `README.md`, `docs/STATE.md`, `docs/VERIFICATION.md` and the claim
   wording agree with `labels-v3` and the 147-quarter window. Shravani has checked the label
   docs and Palchhin the results docs.
4. **Dry-run evidence.** Arshiya's clean clone of current `main` is recorded; the packaging
   checklist is complete; nothing is bundled, mirrored, zipped or tagged.
5. **Integration rehearsal.** The fixed merge order has been tried once; each owner knows
   which branch they merge and which checks follow.
6. **Plain-English pitch.** One page: what was built, what the label proves, what the model
   result does not prove, and what is next. No forecast claim before out-of-sample results.
7. **A PR on `feat/india-scope-docs`** with commands, tests, hashes and known gaps.

### How your lane is judged

- **Scope gate:** India is Label-B-only under O-2; the 6-of-8 rule is unchanged; no
  country is quietly promoted.
- **Claim gate:** no forecast claim before out-of-sample results; caveats present; the
  negative-result path is described honestly.
- **Integration gate:** the merge order works, each owner merges their own branch, and no
  check is silently skipped.
- **Release gate:** nothing is packaged, mirrored, zipped or tagged without explicit
  approval.
- **Work balance:** you coordinate rather than absorb. If a lane is behind, the owner says
  so and the team re-plans; you do not quietly finish it yourself.

## 5. How your work combines with the others

| Hand-off | When | What must be true |
|---|---|---|
| H1: you → all | Day 1 morning | Everyone can state their Day 1 task from `docs/team/` and `docs/TEAM_PLAN.md` |
| H3: Shravani → you | Day 5 end | Japan label + chronology note + Germany 6/8 decision; hashes recorded |
| H4: Arshiya → Palchhin + you | Day 4 end (final folds); Day 5 end (frozen) | Table + final folds available for the USA headline; frozen files and leakage tests complete |
| H5: Palchhin → you | Day 5 end | USA headline, episode, ablation and ensemble tables; C-13 applied once |
| H6: all → you + Arshiya | Day 6 morning | One branch per lane, green checks, short hand-off note |
| Day 6 merge | Steps 1–4 | Shravani merges labels, Arshiya features/folds, Palchhin models, you docs; checks after each |
| Day 7 review | — | Cross-review, combined clean clone (Arshiya runs, you record), then go/no-go |
| H7: you + Arshiya → all | Day 7 morning | Clean-clone evidence, hash table, draft go/no-go |

Your lane is the glue. You do not need to be the best at labels, features or models; you
need the whole thing to be consistent, reproducible and honestly described.

## 6. DOs

- **DO** read the four lane briefs and the team plan before Day 1.
- **DO** record an access failure exactly; a blocked download is evidence, not a reason to
  invent a proxy.
- **DO** keep India Label-B-only under O-2 and keep the 6-of-8 rule unchanged.
- **DO** delegate verification: Arshiya owns the combined clean clone, Palchhin the results
  docs, Shravani the label docs.
- **DO** let each lane owner merge their own branch in the fixed order.
- **DO** run the checks after every merge and write down the result.
- **DO** keep the pitch plain: what was built, what it proves, what it does not prove.
- **DO** record every rule change before results, with a date and a reason.
- **DO** ask for help early and escalate a slipping lane at the stand-up.
- **DO** keep the final package behind explicit approval.

## 7. DON'Ts

- **DON'T** absorb another lane's unfinished work silently. Coordinate, re-plan, or record
  the gap.
- **DON'T** relax the 6-of-8 rule, O-2 or the ensemble rule to make the story cleaner.
- **DON'T** substitute a proxy for missing India data or present the pre-audit as final.
- **DON'T** claim a forecast before out-of-sample results exist.
- **DON'T** change a frozen label, a fold boundary, the estimator or the eight-indicator
  structure without a new version and a recorded decision.
- **DON'T** create a bundle, mirror, zip or release tag without explicit approval.
- **DON'T** hand-edit generated artefacts; regenerate them.
- **DON'T** merge a red branch or hide a failed check.
- **DON'T** let the Day 4 dry run stand in for the Day 7 combined clean clone.

## 8. Allowed creative liberty and educational freedom

Inside the guardrails, you have room to make the project better:

- **Choose the pitch format.** A one-pager, a short slide deck, a narrative README section
  or a spoken walkthrough are all fine; keep the claims accurate.
- **Add useful extras.** An India source table, a decision timeline, a glossary, a
  "what we learned" page or a short integration checklist are welcome.
- **Learn while you work.** You may spend up to about half a day (roughly 10% of the lane)
  on integration tooling, reproducibility, writing or a scope question. Note it in your
  hand-off.
- **Improve the integration process** — a cleaner merge checklist, a hash table, a
  one-command verification script — as long as the checks themselves do not weaken.
- **Propose a scope improvement** before results if you think it is defensible. The team
  decides and records it; it does not become a silent exception.
- **Write a "what I learned" section** in the final note. It helps the next cohort.

## 9. If you get stuck

1. **India access is blocked?** Record the exact failure, the URL and the date, then stop.
   A documented failure is the deliverable.
2. **A lane slips?** Say so at the stand-up and re-plan the Day 5 hand-off. Do not hide it
   until Day 6.
3. **Docs disagree?** Find the single source of truth (`config/scope.yaml`, `labels-v3`,
   the frozen hashes) and fix the prose to match it.
4. **A merge turns red?** Stop; the owner fixes their branch before the next merge. Do not
   patch around it on `main`.
5. **Someone asks for a package?** Confirm explicit approval first, then follow the
   packaging checklist. Otherwise write findings and next actions.

## 10. Where to look

| Need | File |
|---|---|
| The plan | `docs/TEAM_PLAN.md`, `Team_Plan.xlsx` |
| Current state and hashes | `docs/STATE.md` |
| Frozen rules | `docs/BUILD_CONTRACT.md` |
| Ensemble and claim wording | `docs/PROPOSAL_ADDENDUM.md` |
| India pre-audit | `docs/INDIA_COVERAGE_AUDIT.md` |
| Decisions | `docs/DECISIONS.md`, `decisions_log.csv` |
| Verification evidence | `docs/VERIFICATION.md` |
| Lane briefs | `docs/team/01_shravani_japan_germany.md`, `02_arshiya_features_harness.md`, `03_palchhin_models_ensemble.md` |
| Weekly log | `EWS_Work_Log.xlsx` |
| Scope and sources | `config/scope.yaml`, `data/scope.csv` |

---

**Bottom line:** close India honestly, keep the scope and the words precise, and coordinate
a merge where each owner carries their own lane. A documented access failure and a clean
go/no-go are successful outcomes; an overclaimed package is not.
