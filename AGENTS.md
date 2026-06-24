# AGENTS.md

## Project: World Cup Oracle

World Cup Oracle is a full-stack World Cup simulation and prediction platform. The goal is to simulate the FIFA World Cup many times using statistical and machine learning models, then show team probabilities, stage probabilities, group outcomes, knockout paths, upset risk, and what-if scenarios.

## Core Product Goals

The app should support:

1. Monte Carlo tournament simulation.
2. Group-stage simulation with realistic standings.
3. Round-of-32 qualification logic for the 48-team World Cup format.
4. Knockout simulation with extra time and penalty outcomes.
5. Champion probabilities.
6. Stage probabilities for every team.
7. Group qualification probabilities.
8. Best third-place team tracking.
9. What-if scenario simulation.
10. Probability movement after real or manual results.
11. Team path explorer.
12. Upset radar.
13. Group chaos score.
14. Model comparison.
15. Backtesting on past tournaments.

## Tech Stack

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts or ECharts
- TanStack Table

Backend:

- FastAPI
- Python
- NumPy
- Pandas
- SciPy
- scikit-learn
- Pydantic
- pytest

Database:

- SQLite for early development.
- Postgres can be introduced later.

## Coding Rules

- Do not make broad unrelated changes.
- Keep each task focused.
- Prefer small, reviewable commits.
- Write tests for simulation logic.
- Use type hints in Python.
- Use Pydantic models for API request/response schemas.
- Keep business logic separate from API route handlers.
- Keep frontend UI components separate from data-fetching code.
- Do not hardcode tournament logic inside React components.
- Do not hardcode model logic inside API routes.
- Do not introduce heavy dependencies unless clearly justified.
- Keep generated data files small unless the task explicitly requires large data.

## Simulation Rules

The tournament simulation engine must be deterministic when a random seed is provided.

The engine should separate:

- input data
- match model
- tournament rules
- simulation runner
- aggregation logic

The simulation engine should support:

- already-played matches
- manually overridden what-if results
- simulated future group matches
- simulated future knockout matches
- group tables
- third-place ranking
- stage progression counts
- probability aggregation

Do not simplify the World Cup format incorrectly. The tournament format includes:

- 48 teams
- 12 groups of 4
- top 2 teams from each group qualifying
- best 8 third-place teams qualifying
- Round of 32
- knockout rounds until champion

## Modeling Rules

Start simple and extend gradually.

Model order:

1. Elo baseline.
2. Elo-derived win/draw/loss model.
3. Poisson scoreline model.
4. Dixon-Coles style adjustment if needed.
5. ML model.
6. Ensemble model.

Do not build ML before the simulation engine is correct.

## Testing Requirements

Write tests for:

- group table calculation
- points calculation
- goal difference
- goals scored
- group ranking
- third-place qualification
- deterministic simulation with fixed seed
- knockout winner generation
- aggregation of simulation results

For every major feature, add or update tests before considering the task complete.

## Git Rules

Before making changes:

- inspect the current repo structure
- inspect existing tests
- understand existing models and schemas

After making changes:

- run `bash scripts/clean_pycache.sh` before commits and after local test runs
- run relevant tests
- summarize changed files
- summarize test results
- mention any assumptions

## Git Workflow

Never commit directly to main or dev.

For every feature, bug fix, or chore:
1. Branch from the current base branch: `git checkout -b <type>/<short-name>`
2. Make changes in small, focused commits.
3. Open a pull request targeting the base branch.
4. Review the diff yourself (or request a reviewer) before merging.
5. Merge via PR only — no direct pushes to main or dev.

Branch naming: `feat/`, `fix/`, `chore/`, `refactor/`, `test/`

## Repo hygiene

- Never commit `__pycache__/`, `*.pyc`, or `.pytest_cache/` directories.
- Root `.gitignore` blocks these artifacts.
- **Agents:** run `bash scripts/clean_pycache.sh` at the start of Python work and again after tests — do not wait for the user to ask.
- `pytest` auto-runs cache cleanup via `apps/api/conftest.py`.
- Optional (local): run `bash scripts/install-git-hooks.sh` once to clear caches on every commit.

## Communication Style

When completing a task, provide:

1. What changed.
2. Files changed.
3. How to test it.
4. Any known limitations.
5. Recommended next task.

Do not claim something is complete if it is only partially implemented.
