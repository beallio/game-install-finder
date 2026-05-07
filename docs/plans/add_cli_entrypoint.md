# CLI Entrypoint

## Problem Definition

Users currently need to invoke the tool with `python -m game_path_finder.game_path_finder`, which
is verbose and easy to confuse with filesystem paths. The project should expose a normal CLI
command that can be run through uv.

## Architecture Overview

Add a packaging console script entry point in `pyproject.toml` that points to the existing
`main()` function in `game_path_finder.game_path_finder`. No runtime CLI behavior needs to move.

## Core Data Structures

No production data structures change. The packaging metadata gains a `project.scripts` mapping.

## Public Interfaces

Add this command:

```bash
game-path-finder
```

It should accept the same options as the existing module invocation.

## Dependency Requirements

No new dependencies are required.

## Testing Strategy

Add a protocol test that parses `pyproject.toml` and requires the `game-path-finder` script to
point at `game_path_finder.game_path_finder:main`. Run that test red before changing project
metadata, then validate the actual command with `./run.sh uv run game-path-finder --help`.
