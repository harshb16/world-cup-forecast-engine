# PLANS.md

## Current Milestone

Milestone 2: Data credibility, model transparency, validation, and product polish

## Product Phases

### Phase 1: Core simulation engine

- Team model
- Match model
- Group model
- Tournament state
- Group standings
- Top-two qualification
- Third-place ranking
- Knockout simulation
- Monte Carlo aggregation

Status: complete for MVP.

### Phase 2: Backend API

- FastAPI setup
- `/simulate` endpoint
- `/teams` endpoint
- `/fixtures` endpoint
- `/scenario` endpoint
- `/metadata` endpoint

Status: complete for MVP.

### Phase 3: Frontend dashboard

- Champion odds table
- Stage probability table
- Group probability cards
- Team pages
- What-if lab

Status: complete for MVP.

### Phase 4: Real data foundation

- Checked-in processed World Cup 2026 teams, groups, fixtures, results, ratings
- Processed data validator
- Data source metadata
- Backend defaults to processed data
- Sample data retained for tests and development fallback

Status: complete for MVP.

### Phase 5: Product foundation hardening

- Data quality counts and coverage metadata
- Public model assumptions and limitations
- Baseline backtesting metrics
- Clear UI copy for current model/data limits
- Removal of placeholder product pages

Status: current.

### Phase 6: Better tournament rules

- Official Round-of-32 bracket mapping
- More explicit knockout path tracking
- More robust third-place matchup handling
- Probability movement after ingested real results

Status: next rules sprint.

### Phase 7: Better models

- Elo calibration
- Poisson calibration
- Dixon-Coles style score correction
- Historical feature dataset
- ML model
- Ensemble model

Status: deferred until data and evaluation foundation are stronger.

### Phase 8: Live updates

- Real results ingestion
- Probability timeline
- Biggest risers/fallers
- Published update workflow

Status: future.
