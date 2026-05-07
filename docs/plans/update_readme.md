# README Documentation Update

## Problem Definition

The current README still contains scaffold placeholders and does not document what the
`game_path_finder` tool actually does, how to run it, which platforms it searches, what JSON it
returns, or which dependencies it requires.

## Architecture Overview

This is a documentation-only change. The README should describe the existing CLI implemented in
`src/game_path_finder/game_path_finder.py` without changing runtime behavior.

## Core Data Structures

The README should document the `SteamGame` JSON fields exposed by the CLI:

- `appid`
- `name`
- `installdir`
- `path`
- `exists`
- `library`
- `manifest`

## Public Interfaces

Document the current command-line options:

- `--steam-path`
- `--steam-root PATH`
- `--list-games`
- `--app-id APPID`
- `--appid-from-name NAME`
- `--pretty`
- `--debug`

## Dependency Requirements

Document Python 3.12 or newer for the project, `uv` for environment management, and `vdf` as the
runtime dependency used to parse Steam VDF/ACF files.

## Testing Strategy

Add a protocol-level README test that requires the README to contain concrete project description,
installation, usage examples, dependency requirements, CLI options, and JSON output documentation.
Run it red against the placeholder README, then update README until the suite passes.
