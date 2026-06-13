# Tournament Rules

World Cup 2026 format:

- 48 teams.
- 12 groups of 4.
- Each group plays round-robin.
- Top 2 teams in each group qualify.
- Best 8 third-place teams qualify.
- Round of 32 starts knockout phase.

Current implementation:

- Group-stage data is processed from real World Cup 2026 structure.
- Knockout simulation uses the FIFA World Cup 2026 Round-of-32 match slots.
- Third-place qualifiers are assigned only to slots that allow their source group,
  using deterministic matching when multiple valid third-place assignments exist.
