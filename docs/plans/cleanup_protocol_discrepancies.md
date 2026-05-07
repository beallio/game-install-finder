# Protocol Discrepancy Cleanup

## Problem Definition

The repository contains artifacts that conflict with the project-local agent protocol:

- A tracked `.geminiignore` file, despite `AGENTS.md` requiring that generated agent
  instructions avoid Gemini-specific files.
- Python bytecode cache directories and `.pyc` files under `src/` and `tests/`, despite
  the cache isolation policy requiring generated caches to live under `/tmp/game_path_finder`.

## Architecture Overview

This is a repository hygiene change. No package behavior or runtime architecture changes are
required. The fix removes the protocol-violating artifacts and adds protocol tests that fail if
they reappear.

## Core Data Structures

No production data structures are affected. The tests use `pathlib.Path` collections to identify
forbidden paths.

## Public Interfaces

No public Python interfaces change.

## Dependency Requirements

No dependency changes are required. Existing project tooling in `pyproject.toml` and `uv.lock`
is sufficient.

## Testing Strategy

Add protocol tests that assert:

- `.geminiignore` is absent from the repository root.
- `src/` and `tests/` do not contain `__pycache__` directories or `.pyc` files.

Verify the tests fail before cleanup, then remove the violating artifacts and run the required
validation suite through `./run.sh`.
