# Add Version Flag

## Problem Definition

The command-line tool exposes `__version__` as package metadata but does not provide a CLI flag for
users and release smoke tests to print the installed tool version.

## Architecture Overview

Add an argparse `--version` flag to the existing parser in `src/game_install_finder/cli.py`. The
flag should use the package version already resolved by `game_install_finder._version` so installed
packages, editable installs, and source checkouts report the same value.

## Core Data Structures

- No new persistent data structures are required.
- The parser will use the existing `__version__` string from `src/game_install_finder/_version.py`.

## Public Interfaces

- Add `game-install-finder --version`.
- The command prints `game-install-finder <version>` and exits with status code `0`.
- The help output documents `--version`.

## Dependency Requirements

No new dependency is required. Version lookup continues to use `importlib.metadata`.

## Testing Strategy

- Add a parser-level regression test for `--version` output and exit behavior.
- Verify help output includes the new flag without disrupting existing help formatting.
- Run the full repository validation suite through `./run.sh`.
