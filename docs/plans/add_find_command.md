# Add Find Command

## Problem Definition

The CLI currently exposes separate flags for exact Steam appid lookup and fuzzy name lookup:
`--app-id` and `--appid-from-name`. Users need a shorter command that chooses the lookup mode from
the provided query.

## Architecture Overview

Add an optional `find QUERY` command shape to the existing parser without removing the current flags.
The command will reuse the same lookup paths already used by `--app-id` and `--appid-from-name`.
Digits-only queries use appid lookup. Every other query uses fuzzy name lookup.

## Core Data Structures

- No persistent data structures are required.
- Parsed CLI arguments gain an optional command token and query token.
- Fuzzy name lookup continues to use `cutoff_score` and the existing result fields.

## Public Interfaces

- Add `game-install-finder find 730`.
- Add `game-install-finder find "counter strike"`.
- Numeric `find` queries emit the existing appid lookup fields: `game` and `app_path`.
- Non-numeric `find` queries emit the existing fuzzy lookup fields: `match`, `candidates`, and
  `score`.
- Existing flags remain supported for backward compatibility.

## Dependency Requirements

No new dependency is required. The implementation uses `argparse` and existing lookup helpers.

## Testing Strategy

- Add CLI regression tests for numeric `find` routing to appid lookup output.
- Add CLI regression tests for text `find` routing to fuzzy name lookup output.
- Add parser/help coverage for the new command shape.
- Run validation through `./run.sh`.
