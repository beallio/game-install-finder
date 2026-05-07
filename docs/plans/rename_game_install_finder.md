# Rename to game-install-finder

## Problem Definition

The project has been prepared for the final `game-install-finder` identity, which fits the intended
product direction of local game install discovery across multiple launchers. The package metadata,
CLI, import package, documentation, cache paths, and release workflow should all use that identity.

## Architecture Overview

This is a project identity and packaging rename. The Steam implementation remains the only
launcher backend for now, but the public project name, import package, CLI command, documentation,
and release metadata should move to cross-launcher naming.

## Core Data Structures

No runtime data structures change. Existing Steam game metadata records and JSON output stay
compatible.

## Public Interfaces

The public CLI command becomes:

```bash
game-install-finder
```

The Python import package becomes:

```python
import game_install_finder
```

## Dependency Requirements

No runtime dependencies are added. Packaging and publishing should use `uv build --no-sources` and
`uv publish` in GitHub Actions.

## Testing Strategy

Add failing tests before implementation to require:

- PyPI project name `game-install-finder`.
- A non-placeholder PyPI description.
- Console script `game-install-finder`.
- Import package `game_install_finder`.
- README and cache paths updated to the new name.
- GitHub Actions workflow configured for PyPI Trusted Publishing with uv.
