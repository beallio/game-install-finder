# Add Cutoff Score Flag

## Problem Definition

Fuzzy name lookup always uses the built-in confidence threshold. Users need a command-line flag to
raise or lower the minimum accepted fuzzy score so low-confidence matches can be suppressed.

## Architecture Overview

Add a parser option in `src/game_install_finder/cli.py` named `--cutoff-score`. The option will be a
floating-point value used by fuzzy lookup. The fuzzy matcher will keep its current default threshold
when the option is omitted, and callers can pass a custom threshold when they need stricter or looser
matching.

## Core Data Structures

- No persistent data structures are required.
- `fuzzy_match_game` will accept a `cutoff_score` float and compare the best score against it.
- The existing JSON output fields remain `match`, `candidates`, and `score`.

## Public Interfaces

- Add `game-install-finder --appid-from-name NAME --cutoff-score SCORE`.
- `SCORE` is parsed as a float.
- If the best fuzzy score is lower than `SCORE`, `match` is `null`.
- `candidates` and `score` are still returned so callers can inspect suppressed results.
- Existing behavior remains unchanged when `--cutoff-score` is omitted.

## Dependency Requirements

No new dependency is required. The implementation uses `argparse` and existing fuzzy matching code.

## Testing Strategy

- Add a matcher-level regression test proving a custom cutoff suppresses a low-scoring match.
- Add a CLI-level regression test proving `--cutoff-score` affects JSON output for
  `--appid-from-name`.
- Add a help-output assertion documenting the new option.
- Run validation through `./run.sh`.
