# Heroic and Lutris Search

## Problem Definition

`game-install-finder` currently indexes Steam installs only. The package name and CLI now target
game install discovery across PC game launchers, so list and fuzzy search workflows should discover
installed games from Steam, Heroic, and Lutris while preserving existing Steam appid behavior.

## Architecture Overview

Introduce a launcher-neutral installed-game record used by all indexing and lookup paths. Steam
discovery keeps the current VDF parsing and library traversal, but emits launcher-aware records.
Heroic discovery reads local Legendary/Heroic installed metadata JSON files from explicit and
detected config roots. Lutris discovery reads the local `pga.db` SQLite database from explicit and
detected data roots.

The CLI will build indexes for the selected launcher set and then apply list, appid, and fuzzy
lookup actions over that shared record shape. Steam appid lookup remains Steam-only.

## Core Data Structures

- `InstalledGame`: launcher-neutral installed game record.
- Fields shared by all launchers: `launcher`, `name`, `path`, `exists`, and `source`.
- Steam compatibility fields: `appid`, `installdir`, `library`, and `manifest`.
- Fuzzy results: unchanged dictionary shape with `match`, `candidates`, and `score`, where
  `match` is an `InstalledGame`.

## Public Interfaces

- `--launcher steam|heroic|lutris|all`: selects which launchers are indexed. Defaults to `all`.
- `--heroic-root PATH`: reads Heroic/Legendary metadata from an explicit config root.
- `--lutris-root PATH`: reads Lutris metadata from an explicit data root.
- `--list-games`: emits records that include `launcher`.
- `--appid-from-name NAME`: searches across selected launchers by default.
- `--app-id APPID`: remains Steam-only and returns no match when Steam is excluded.

## Dependency Requirements

No new runtime dependency is planned. Heroic metadata is JSON and can use `json`; Lutris metadata
is SQLite and can use the standard library `sqlite3`. Existing Steam support continues to use
`vdf`.

## Testing Strategy

Use fixture directories and temporary databases so tests do not depend on installed launchers.
Cover the Steam model transition first, then CLI launcher filtering, Heroic JSON discovery, Lutris
SQLite discovery, combined cross-launcher listing and fuzzy search, and README/protocol language.
Malformed Heroic and Lutris metadata must be non-fatal and warn only when `--debug` is enabled.
