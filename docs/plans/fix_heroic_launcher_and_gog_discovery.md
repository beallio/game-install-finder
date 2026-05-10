# Fix Heroic Launcher And GOG Discovery

## Problem Definition

Two Steam Deck Heroic workflows fail:

- `game-install-finder --launcher heroic` returns only `{"steam_path": null}` instead of listing
  Heroic games.
- Heroic GOG installs in `gog_store/installed.json` use an `installed: [...]` container shape that
  is not converted into installed-game records.

The same installed-list shape may also be used by other Heroic store integrations, so the fix should
be store-agnostic where possible.

## Architecture Overview

Keep the public JSON record shape unchanged. Treat a launcher-only invocation as a request to list
games for that launcher. Extend Heroic metadata normalization so `installed` arrays are parsed like
existing list and `games` array sources. Continue filtering to locally present paths only.

## Core Data Structures

- `InstalledGame`: unchanged output record.
- Heroic metadata files: include explicit known store `installed.json` locations plus recursive
  fallback.
- Heroic entry normalization: support top-level `installed: [...]`, `games: [...]`, raw lists, and
  keyed dictionaries.

## Public Interfaces

- `game-install-finder --launcher heroic` lists Heroic games, equivalent to selecting Heroic and
  requesting the installed-games list.
- `build_heroic_index()` includes installed records from Heroic store directories such as
  `gog_store/installed.json` when the resolved install path exists.

## Dependency Requirements

No new dependency is required. Parsing remains standard-library JSON.

## Testing Strategy

- Add a red test for launcher-only Heroic CLI invocation returning `games`.
- Add a red test for `gog_store/installed.json` with top-level `installed` records.
- Preserve existing Heroic sideload, store cache, Steam, Lutris, and fuzzy search behavior.
- Run the full repository validation suite through `./run.sh`.
