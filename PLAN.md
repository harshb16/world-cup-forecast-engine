# Tournament Time Machine — Phased Implementation Plan

## Summary

Build a global, shareable replay mode using `?at=<milestone_id>`. Each milestone will be a deterministic reconstruction using the frozen final dataset and model, with only results known at that point revealed.

Nine milestones:

1. `before_group_md1`
2. `after_group_md1`
3. `after_group_md2`
4. `after_group_md3`
5. `after_round_of_32`
6. `after_round_of_16`
7. `after_quarter_finals`
8. `after_semi_finals`
9. `after_final`

Snapshots will be precomputed from 100,000 simulations per milestone. No Monte Carlo work runs during page requests.

## Phase 0 — Baseline and Branch

- Create `feat/tournament-time-machine` from the current base branch.
- Run `bash scripts/clean_pycache.sh`.
- Record current API test, frontend lint, and frontend build results.
- Preserve all existing behavior when no `at` query parameter is present.
- Use small, phase-aligned commits and open a PR rather than merging directly.

Acceptance gate: existing tests and builds have a recorded baseline before feature work.

## Phase 1 — Milestone Domain and Tournament Slicing

- Promote the existing private milestone logic into a reusable time-machine service.
- Define milestone metadata: ID, label, display order, phase, cutoff, known-result count, availability, previous ID, and next ID.
- Mark a milestone available only when its complete matchday or knockout round has finished; partial rounds must not appear as completed.
- Implement `slice_tournament_at_milestone()`:
  - Keep all scheduled group fixtures, but clear results after the selected cutoff.
  - Preserve only knockout fixtures known through the selected round.
  - Remove later real knockout pairings entirely to prevent future-information leakage.
  - Preserve teams, ratings, groups, and the frozen model version.
- Derive a deterministic seed from data version, model version, and milestone ID.
- Label every replay as reconstructed, not an original historical publication.

Acceptance gate: unit tests prove that future scores, winners, and knockout pairings cannot leak into an earlier milestone.

## Phase 2 — Precomputed Artifact Pipeline

- Refactor bank and forecast aggregation services to accept an explicit sliced `TournamentConfig` instead of reloading the latest tournament internally.
- Ensure summary probabilities, bracket, group chaos, upset radar, third-place tracking, team paths, and head-to-head calculations all use the same milestone bank.
- Add an offline generator with:
  - Default `WCO_TIME_MACHINE_SIMULATIONS=100000`.
  - Lower simulation counts for tests and local iteration.
  - Progress output by milestone.
  - Atomic writes.
  - Resume support when artifact fingerprints already match.
  - `--force` and `--require-complete` options.
- Generate this layout:

```text
time_machine/
├── manifest.json
└── milestones/
    └── <milestone_id>/
        ├── snapshot.json
        ├── team_paths.json
        └── bank.npz
```

- Each snapshot contains:
  - Milestone metadata and provenance.
  - Existing `ForecastSnapshotResponse`.
  - Actual group tables as known at that milestone.
  - Milestone-sliced fixtures.
  - Probability movers versus the previous milestone.
- Record data version, model version, seed, simulation count, artifact size, and checksum in the manifest.
- Extend the freeze script to run the generator with `--require-complete` and copy the whole directory into the `wc2026` archive.
- Do not rebuild all milestones during normal live result sync; regeneration remains an explicit offline operation.

Acceptance gate: all artifacts for a milestone share identical seed, model, data version, and simulation count, and produce identical output when regenerated.

## Phase 3 — Read-Only API

Add:

- `GET /time-machine/milestones`
  - Returns archive provenance and the ordered milestone catalog.
- `GET /time-machine/milestones/{milestone_id}`
  - Returns the precomputed milestone snapshot.
- `GET /time-machine/milestones/{milestone_id}/team-path/{team_id}`
  - Returns the milestone-specific existing `TeamPathResponse`.
- `GET /time-machine/milestones/{milestone_id}/head-to-head`
  - Accepts `team_a` and `team_b` and calculates meeting odds from that milestone’s bank.

Behavior:

- Never run simulations during these requests.
- Return 404 for unknown or unavailable milestones and teams.
- Return 503 when artifacts are missing or stale relative to the active archive.
- Make `/analytics/probability-history` derive its lightweight chart data from time-machine artifacts when available.
- In archive mode, missing time-machine artifacts must produce an explicit error instead of falling back to request-time simulation.

Acceptance gate: endpoint tests verify response shapes, invalid IDs, stale archives, determinism, and the absence of request-time Monte Carlo execution.

## Phase 4 — Global Replay State and Transport

- Add a `TimeMachineProvider` around the app shell.
- Read the selected milestone exclusively from `?at=...`; do not use local storage.
- Preserve unrelated query parameters such as team comparison IDs.
- Use `router.replace` when scrubbing so browser history is not filled with every milestone.
- Cache loaded snapshots and team paths in memory and prefetch adjacent milestones.
- Preserve `at` when navigating among supported surfaces:
  - Dashboard
  - Groups
  - Bracket
  - Teams
  - Team detail
  - Team comparison
- Navigating to What-if, Matchday, Models, Methodology, Retrospective, or Data Status exits replay mode because those surfaces remain outside this version.

Add a persistent replay transport beneath the header:

```text
[Previous] [Play]  Kickoff ●──●──●──●──●──●──●──●──● Final  [Next]
                           Selected: After Matchday 2
```

- Desktop: full nine-node track grouped into group and knockout phases.
- Mobile: milestone select with previous/play/next controls.
- Autoplay advances every 2.5 seconds, stops at the final, and pauses after manual interaction.
- Respect `prefers-reduced-motion`; data transitions become instant when enabled.
- Invalid shared milestone links fall back to the closest available prior milestone and announce the correction through an accessible status message.

Acceptance gate: refreshing or sharing any supported URL reproduces the same milestone across the entire surface.

## Phase 5 — Integrate Product Surfaces

### Time Machine landing page

- Replace Timeline with `/time-machine`; permanently redirect `/timeline`.
- Change the navigation label from “Timeline” to “Replay.”
- Default `/time-machine` to `before_group_md1`.
- Show:
  - Champion-probability arc.
  - Selected milestone summary.
  - Known-result count.
  - Biggest risers and fallers.
  - Current forecast leader.
  - Links to open Dashboard, Groups, Bracket, and Teams at the selected milestone.
- Clearly display: “Reconstructed with the frozen archive model; not the original published forecast.”

### Dashboard

- Read the selected milestone forecast from the provider.
- Replace live wording with “At this point” replay wording.
- Hide refresh, sync, and data-freshness controls while replaying.
- Use milestone-specific movers, upsets, chaos, final projection, and probabilities.

### Groups

- Display actual W-D-L, goals, goal difference, and points known at the milestone.
- Keep forecast qualification probabilities alongside observed standings.
- Show zeroed standings before kickoff and frozen final standings after Matchday 3.

### Bracket

- Use the milestone’s stored forecast bracket.
- Reset revealed matches when the milestone changes.
- Hide Random, New seed, Refresh, and Sync during replay because they would break archive consistency.
- Keep forecast reveal, export, and match-detail interactions.

### Teams and paths

- Use milestone probabilities on team lists and detail pages.
- Preserve `at` in team and comparison links.
- Load milestone-specific team paths lazily.
- Base “still in” and “eliminated” labels on the selected milestone, not the final state.
- Use the milestone bank for team-comparison head-to-head odds.

Acceptance gate: changing one milestone updates every supported surface without showing any latest-state data.

## Phase 6 — Testing, Archive Generation, and Handoff

Backend tests:

- Exact nine-milestone order and IDs.
- Complete-round availability rules.
- No future-result or knockout-pairing leakage.
- Deterministic seed and artifact generation.
- Forecast, bracket, paths, and head-to-head bank coherence.
- Final milestone produces the recorded champion with probability 1.
- Missing, corrupt, stale, and unavailable artifact responses.
- Freeze manifest includes and verifies all time-machine files.
- Existing non-replay APIs remain unchanged.

Frontend verification:

- Run ESLint and production build.
- Browser-test at approximately 1440px, 1024px, and 390px widths.
- Verify keyboard navigation, focus states, screen-reader labels, autoplay controls, and reduced motion.
- Test shared URLs, refreshes, invalid milestones, browser back, adjacent prefetching, and replay exit.
- Confirm bracket reveal state resets after milestone changes.
- Confirm no API request triggers simulation and warm snapshot reads remain below 200ms locally.

Delivery:

- Generate development artifacts with a reduced count for QA.
- After the final result is recorded, regenerate all nine with 100,000 simulations.
- Run the extended freeze script and validate archive mode.
- Update README and engine documentation with replay semantics, generation commands, storage impact, and limitations.
- Self-review the diff, rerun relevant tests, clean Python caches, and open the PR.

## Public Interface Changes

New backend types:

- `TimeMachineManifestResponse`
- `TimeMachineMilestoneResponse`
- `TimeMachineSnapshotResponse`
- `TimeMachinePhase = pre_tournament | group_stage | knockout | complete`

New frontend API helpers:

- `fetchTimeMachineManifest()`
- `fetchTimeMachineSnapshot(milestoneId)`
- `fetchTimeMachineTeamPath(milestoneId, teamId)`
- `fetchTimeMachineHeadToHead(milestoneId, teamA, teamB)`

The existing forecast and team-path response types remain embedded and backward compatible.

## Assumptions and Boundaries

- This version is a consistent replay using the final frozen model and dataset, not a claim about the exact forecast originally published.
- Granularity is deliberately limited to nine major milestones; match-day and match-by-match replay are deferred.
- What-if scenarios, random brackets, current model evaluation, and operator pages remain outside replay mode.
- Keeping milestone banks is intentional so paths and head-to-head odds remain coherent; expected archive growth is roughly 20–45 MB.
- No new frontend testing framework is introduced; frontend validation uses lint, production build, and browser QA, while domain and API behavior receives pytest coverage.
