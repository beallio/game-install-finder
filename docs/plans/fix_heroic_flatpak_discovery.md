# Fix Heroic Flatpak Discovery

## Problem Definition

Heroic discovery currently reads `installed.json` metadata and misses Steam Deck Flatpak sideload
games stored in `sideload_apps/library.json`. Games such as Wolverine, Deadpool, and Transformers
can be locally installed but absent from `installed.json`, so `--launcher heroic --list-games`
returns an incomplete list.

## Architecture Overview

Extend the existing Heroic metadata scan in `src/game_install_finder/cli.py` without changing the
public `InstalledGame` output shape. Heroic roots should contribute records from known metadata
files, normalize the different JSON container shapes into game entries, resolve paths in a stable
priority order, and only return records whose resolved install directories exist.

## Core Data Structures

- `InstalledGame`: unchanged public record used by Steam, Heroic, and Lutris discovery.
- Heroic metadata file list: explicit paths for `installed.json`, `sideload_apps/library.json`,
  and store cache library files, plus recursive `installed.json` compatibility.
- Heroic entry tuples: `(key, entry, source_file)` where `key` can supply fallback appid metadata.

## Public Interfaces

- `build_heroic_index(heroic_root: Path | None = None, *, debug: bool = False) -> list[InstalledGame]`
  remains the public discovery function.
- CLI output remains unchanged: Heroic records keep `launcher`, `appid`, `name`, `path`, `exists`,
  and `source`, with Steam-only fields left `null`.

## Dependency Requirements

No new dependency is required. Heroic JSON parsing continues to use the Python standard library.

## Testing Strategy

- Add red tests for Heroic `sideload_apps/library.json` with `games[]` records.
- Verify absolute `folder_name` paths are used directly.
- Verify relative `folder_name` paths are joined to `defaultSettings.defaultInstallPath`.
- Verify `install.executable` falls back to the executable parent directory.
- Verify installed records are included only when the resolved path exists.
- Verify missing-path and uninstalled sideload records are excluded.
- Run the full validation suite through `./run.sh`.
