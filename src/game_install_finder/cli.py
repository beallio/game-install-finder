#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "vdf",
# ]
# ///
"""
Game Install Finder
===================

A local game install path discovery CLI. Currently supports Steam libraries.

Features
--------
- Cross-platform Steam discovery
- Proper Steam libraryfolders.vdf parsing
- Multi-library support
- Installed game enumeration
- Exact/fuzzy appid lookup
- Structured JSON output
- PEP 723 compatible (`uv run`)

Why this version exists
-----------------------
The lightweight implementations commonly found online tend to:
- incorrectly return `steamapps/common` instead of the real game path
- break against newer Steam VDF formats
- rely on brittle string splitting
- fail with multiple Steam libraries
- incorrectly assume game folder names

This implementation hardens those areas while remaining:
- single-file
- scripting-friendly

Examples
--------
List installed games:
    uv run steam_path_finder.py --list-games --pretty

Find a game by appid:
    uv run steam_path_finder.py --app-id 570 --pretty

Fuzzy match a game:
    uv run steam_path_finder.py --appid-from-name "counter strike"

Machine-readable JSON:
    uv run steam_path_finder.py --list-games

Notes
-----
This tool ONLY sees locally installed games.
It does not query the Steam Web API.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import vdf


FUZZY_MATCH_THRESHOLD = 0.55
LAUNCHERS = ("steam", "heroic", "lutris", "all")


@dataclass(frozen=True)
class InstalledGame:
    launcher: str
    appid: str | None
    name: str | None
    installdir: str | None
    path: Path | None
    exists: bool
    source: Path | None
    library: Path | None = None
    manifest: Path | None = None

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("path", "source", "library", "manifest"):
            value = data[key]
            data[key] = str(value) if value is not None else None
        return data


SteamGame = InstalledGame


def warn(message: str, *, debug: bool) -> None:
    if debug:
        print(f"warning: {message}", file=sys.stderr)


def print_json(data: dict[str, Any], *, pretty: bool) -> None:
    indent = 2 if pretty else None
    print(json.dumps(data, indent=indent))


# ============================================================
# Steam discovery
# ============================================================


def get_steam_path() -> Path | None:
    """
    Locate the Steam installation directory.

    Returns:
        Path to Steam root directory or None.
    """
    system = platform.system()

    if system == "Windows":
        try:
            import winreg

            open_key = getattr(winreg, "OpenKey")
            hkey_current_user = getattr(winreg, "HKEY_CURRENT_USER")
            query_value_ex = getattr(winreg, "QueryValueEx")

            with open_key(
                hkey_current_user,
                r"Software\Valve\Steam",
            ) as key:
                value, _ = query_value_ex(key, "SteamPath")
                path = Path(value)

                if path.exists():
                    return path

        except Exception:
            return None

    elif system == "Linux":
        candidates = [
            Path.home() / ".steam/steam",
            Path.home() / ".local/share/Steam",
            Path.home() / ".var/app/com.valvesoftware.Steam/.steam/steam",
            Path.home() / ".steam/root",
        ]

        for path in candidates:
            if path.exists():
                return path

    elif system == "Darwin":
        path = Path.home() / "Library/Application Support/Steam"

        if path.exists():
            return path

    return None


# ============================================================
# VDF parsing
# ============================================================


def load_vdf_file(vdf_path: Path, *, debug: bool = False) -> dict[str, Any]:
    """
    Load a Valve KeyValues file.
    """
    if not vdf_path.exists():
        return {}

    try:
        with vdf_path.open(encoding="utf-8", errors="ignore") as file:
            loaded = vdf.load(file)
    except (OSError, SyntaxError, ValueError) as exc:
        warn(f"could not parse {vdf_path}: {exc}", debug=debug)
        return {}

    if isinstance(loaded, dict):
        return loaded

    warn(f"unexpected VDF root in {vdf_path}: {type(loaded).__name__}", debug=debug)
    return {}


def parse_libraryfolders_vdf(vdf_path: Path, *, debug: bool = False) -> list[Path]:
    """
    Parse Steam's libraryfolders.vdf safely.

    Modern Steam format resembles:

        "1"
        {
            "path" "/mnt/games/SteamLibrary"
            ...
        }

    Returns:
        List of Steam library root paths.
    """
    libraries: list[Path] = []

    data = load_vdf_file(vdf_path, debug=debug)
    libraryfolders = data.get("libraryfolders", {})

    if not isinstance(libraryfolders, dict):
        warn(f"unexpected libraryfolders shape in {vdf_path}", debug=debug)
        return libraries

    for library in libraryfolders.values():
        if not isinstance(library, dict):
            continue

        value = library.get("path")

        if not isinstance(value, str):
            continue

        path = Path(value)

        if path.exists():
            libraries.append(path)
        else:
            warn(f"Steam library path does not exist: {path}", debug=debug)

    return libraries


def get_library_paths(steam_path: Path, *, debug: bool = False) -> list[Path]:
    """
    Return all detected Steam library paths.

    Includes:
    - primary Steam library
    - secondary mounted libraries
    """
    libraries: list[Path] = [steam_path]

    vdf_path = steam_path / "steamapps" / "libraryfolders.vdf"

    extra = parse_libraryfolders_vdf(vdf_path, debug=debug)

    seen = set()

    deduped = []

    for lib in libraries + extra:
        resolved = str(lib.resolve())

        if resolved not in seen:
            deduped.append(lib)
            seen.add(resolved)

    return deduped


# ============================================================
# Manifest parsing
# ============================================================


def parse_manifest(manifest_path: Path, *, debug: bool = False) -> dict[str, str]:
    """
    Parse a Steam appmanifest ACF file.

    Extracts:
    - appid
    - name
    - installdir
    """
    data = load_vdf_file(manifest_path, debug=debug)
    app_state = data.get("AppState", {})

    if not isinstance(app_state, dict):
        warn(f"unexpected AppState shape in {manifest_path}", debug=debug)
        return {}

    return {
        key: value
        for key in ("appid", "name", "installdir")
        if isinstance(value := app_state.get(key), str)
    }


# ============================================================
# Game indexing
# ============================================================


def build_game_index(steam_path: Path, *, debug: bool = False) -> list[InstalledGame]:
    """
    Enumerate all installed Steam games.

    Returns:
        List of normalized game metadata records.
    """
    results: list[InstalledGame] = []

    for library in get_library_paths(steam_path, debug=debug):
        steamapps = library / "steamapps"

        if not steamapps.exists():
            warn(f"Steam apps directory does not exist: {steamapps}", debug=debug)
            continue

        for manifest in steamapps.glob("appmanifest_*.acf"):
            meta = parse_manifest(manifest, debug=debug)

            if not meta:
                warn(f"skipping manifest with no app metadata: {manifest}", debug=debug)
                continue

            appid = meta.get("appid")
            name = meta.get("name")
            installdir = meta.get("installdir")

            game_path = None

            if installdir:
                game_path = steamapps / "common" / installdir

            results.append(
                InstalledGame(
                    launcher="steam",
                    appid=appid,
                    name=name,
                    installdir=installdir,
                    path=game_path,
                    exists=game_path.exists() if game_path else False,
                    source=manifest,
                    library=library,
                    manifest=manifest,
                )
            )

    return sorted(
        results,
        key=lambda game: (game.name or "").lower(),
    )


# ============================================================
# Heroic discovery
# ============================================================


def _existing_unique_paths(paths: list[Path]) -> list[Path]:
    results: list[Path] = []
    seen: set[str] = set()

    for path in paths:
        if not path.exists():
            continue

        resolved = str(path.resolve())

        if resolved in seen:
            continue

        results.append(path)
        seen.add(resolved)

    return results


def get_heroic_config_roots() -> list[Path]:
    system = platform.system()
    home = Path.home()
    candidates: list[Path] = []

    if system == "Linux":
        candidates.extend(
            [
                home / ".config/heroic",
                home / ".config/legendary",
                home / ".var/app/com.heroicgameslauncher.hgl/config/heroic",
                home / ".var/app/com.heroicgameslauncher.hgl/config/legendary",
            ]
        )
    elif system == "Windows":
        for env_name in ("APPDATA", "LOCALAPPDATA"):
            if env_value := os.environ.get(env_name):
                base = Path(env_value)
                candidates.extend([base / "heroic", base / "legendary"])
    elif system == "Darwin":
        candidates.extend(
            [
                home / "Library/Application Support/heroic",
                home / "Library/Application Support/legendary",
            ]
        )

    return _existing_unique_paths(candidates)


def _heroic_metadata_files(root: Path) -> list[Path]:
    if not root.exists():
        return []

    if root.is_file():
        return [root]

    candidates = [root / "installed.json", root / "legendary" / "installed.json"]

    try:
        candidates.extend(root.rglob("installed.json"))
    except OSError:
        return [path for path in candidates if path.exists()]

    return _existing_unique_paths(candidates)


def _heroic_entries(data: Any) -> list[tuple[str | None, dict[str, Any]]]:
    if isinstance(data, list):
        return [(None, entry) for entry in data if isinstance(entry, dict)]

    if isinstance(data, dict):
        return [(key, value) for key, value in data.items() if isinstance(value, dict)]

    return []


def _first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = data.get(key)

        if isinstance(value, str) and value:
            return value

    return None


def build_heroic_index(
    heroic_root: Path | None = None,
    *,
    debug: bool = False,
) -> list[InstalledGame]:
    roots = [heroic_root] if heroic_root else get_heroic_config_roots()
    games: list[InstalledGame] = []

    for root in roots:
        if root is None:
            continue

        for metadata_file in _heroic_metadata_files(root):
            try:
                data = json.loads(metadata_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                warn(f"could not parse Heroic metadata {metadata_file}: {exc}", debug=debug)
                continue

            for key, entry in _heroic_entries(data):
                name = _first_string(entry, ("title", "name", "app_title", "appName", "app_name"))
                install_path = _first_string(
                    entry,
                    ("install_path", "installPath", "install_dir", "path"),
                )

                if not name or not install_path:
                    continue

                path = Path(install_path).expanduser()
                appid = _first_string(entry, ("app_name", "appName", "app_id", "id", "appid"))

                games.append(
                    InstalledGame(
                        launcher="heroic",
                        appid=appid or key,
                        name=name,
                        installdir=None,
                        path=path,
                        exists=path.exists(),
                        source=metadata_file,
                    )
                )

    return sorted(games, key=lambda game: (game.name or "").lower())


# ============================================================
# Lutris discovery
# ============================================================


def get_lutris_data_roots() -> list[Path]:
    system = platform.system()
    home = Path.home()
    candidates: list[Path] = []

    if system == "Linux":
        candidates.extend(
            [
                home / ".local/share/lutris",
                home / ".var/app/net.lutris.Lutris/data/lutris",
            ]
        )
    elif system == "Windows":
        for env_name in ("APPDATA", "LOCALAPPDATA"):
            if env_value := os.environ.get(env_name):
                candidates.append(Path(env_value) / "lutris")
    elif system == "Darwin":
        candidates.append(home / "Library/Application Support/lutris")

    return _existing_unique_paths(candidates)


def _lutris_database_files(root: Path) -> list[Path]:
    if not root.exists():
        return []

    if root.is_file():
        return [root]

    candidates = [root / "pga.db"]

    try:
        candidates.extend(root.rglob("pga.db"))
    except OSError:
        return [path for path in candidates if path.exists()]

    return _existing_unique_paths(candidates)


def _lutris_path_column(columns: set[str]) -> str | None:
    for column in ("directory", "install_dir", "install_path", "path"):
        if column in columns:
            return column

    return None


def build_lutris_index(
    lutris_root: Path | None = None,
    *,
    debug: bool = False,
) -> list[InstalledGame]:
    roots = [lutris_root] if lutris_root else get_lutris_data_roots()
    games: list[InstalledGame] = []

    for root in roots:
        if root is None:
            continue

        for database_file in _lutris_database_files(root):
            try:
                connection = sqlite3.connect(database_file)
                connection.row_factory = sqlite3.Row

                with connection:
                    table_info = connection.execute("pragma table_info(games)").fetchall()
                    columns = {row["name"] for row in table_info}
                    path_column = _lutris_path_column(columns)

                    if "name" not in columns or path_column is None:
                        warn(
                            f"could not read Lutris metadata {database_file}: "
                            "games table lacks name or install path column",
                            debug=debug,
                        )
                        continue

                    rows = connection.execute("select * from games").fetchall()
            except sqlite3.Error as exc:
                warn(f"could not read Lutris metadata {database_file}: {exc}", debug=debug)
                continue
            finally:
                try:
                    connection.close()
                except UnboundLocalError:
                    pass

            for row in rows:
                name = row["name"]
                install_path = row[path_column]

                if not isinstance(name, str) or not name:
                    continue

                if not isinstance(install_path, str) or not install_path:
                    continue

                if "installed" in row.keys() and not row["installed"]:
                    continue

                path = Path(install_path).expanduser()
                raw_id = row["id"] if "id" in row.keys() else None

                games.append(
                    InstalledGame(
                        launcher="lutris",
                        appid=str(raw_id) if raw_id is not None else None,
                        name=name,
                        installdir=None,
                        path=path,
                        exists=path.exists(),
                        source=database_file,
                    )
                )

    return sorted(games, key=lambda game: (game.name or "").lower())


def build_installed_game_index(
    *,
    steam_root: Path | None = None,
    heroic_root: Path | None = None,
    lutris_root: Path | None = None,
    launcher: str = "all",
    debug: bool = False,
) -> list[InstalledGame]:
    games: list[InstalledGame] = []

    if launcher in ("all", "steam") and steam_root:
        games.extend(build_game_index(steam_root, debug=debug))

    if launcher in ("all", "heroic"):
        games.extend(build_heroic_index(heroic_root, debug=debug))

    if launcher in ("all", "lutris"):
        games.extend(build_lutris_index(lutris_root, debug=debug))

    games = filter_games_by_launcher(games, launcher)

    return sorted(games, key=lambda game: (game.launcher, (game.name or "").lower()))


# ============================================================
# Lookup helpers
# ============================================================


def get_game_by_appid(
    games: list[InstalledGame],
    appid: str,
) -> InstalledGame | None:
    """
    Resolve installed game metadata by appid.
    """
    for game in games:
        if game.launcher == "steam" and game.appid == str(appid):
            return game

    return None


def filter_games_by_launcher(
    games: list[InstalledGame],
    launcher: str,
) -> list[InstalledGame]:
    if launcher == "all":
        return games

    return [game for game in games if game.launcher == launcher]


def normalize_name(name: str) -> str:
    """
    Normalize game names for fuzzy matching.
    """
    name = name.casefold()

    name = name.replace("_", " ")

    name = re.sub(r"[^\w\s]", " ", name)

    name = re.sub(r"\s+", " ", name, flags=re.UNICODE)

    return name.strip()


def fuzzy_match_game(
    query: str,
    games: list[InstalledGame],
) -> dict[str, Any]:
    """
    Perform robust fuzzy matching against installed games.

    Strategy:
    - normalization
    - exact normalized match
    - substring match
    - SequenceMatcher scoring
    - confidence threshold with fallback candidates
    """
    if not games:
        return {
            "match": None,
            "candidates": [],
            "score": 0.0,
        }

    normalized_query = normalize_name(query)

    if not normalized_query:
        return {
            "match": None,
            "candidates": [],
            "score": 0.0,
        }

    scored: list[tuple[float, InstalledGame]] = []

    for game in games:
        name = game.name

        if not name:
            continue

        normalized_name = normalize_name(name)

        if normalized_query == normalized_name:
            return {
                "match": game,
                "candidates": [name],
                "score": 1.0,
            }

        score = SequenceMatcher(
            None,
            normalized_query,
            normalized_name,
        ).ratio()

        if normalized_query in normalized_name:
            score += 0.25

        score = min(score, 1.0)

        scored.append((score, game))

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    candidates = [game.name for _, game in scored[:5] if game.name]

    best_score = scored[0][0] if scored else 0.0
    best_match = scored[0][1] if scored and best_score >= FUZZY_MATCH_THRESHOLD else None

    return {
        "match": best_match,
        "candidates": candidates,
        "score": best_score,
    }


# ============================================================
# CLI
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    """
    Construct CLI parser.
    """
    parser = argparse.ArgumentParser(
        description=("Game install path discovery CLI for Steam, Heroic, and Lutris"),
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            width=100,
            max_help_position=32,
        ),
    )

    parser.add_argument(
        "--steam-path",
        action="store_true",
        help="Return detected Steam installation path",
    )

    parser.add_argument(
        "--steam-root",
        type=Path,
        metavar="PATH",
        help="Use this Steam installation path instead of auto-detection",
    )

    parser.add_argument(
        "--heroic-root",
        type=Path,
        metavar="PATH",
        help="Use this Heroic or Legendary config path instead of auto-detection",
    )

    parser.add_argument(
        "--lutris-root",
        type=Path,
        metavar="PATH",
        help="Use this Lutris data path instead of auto-detection",
    )

    parser.add_argument(
        "--list-games",
        action="store_true",
        help="Enumerate installed games",
    )

    parser.add_argument(
        "--launcher",
        choices=LAUNCHERS,
        default="all",
        metavar="LAUNCHER",
        help="Filter installed games by launcher",
    )

    parser.add_argument(
        "--app-id",
        metavar="APPID",
        help="Lookup installed game by appid",
    )

    parser.add_argument(
        "--appid-from-name",
        metavar="NAME",
        help="Fuzzy match installed game name to appid",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print non-fatal parser/discovery warnings to stderr",
    )

    return parser


# ============================================================
# Main
# ============================================================


def main() -> int:
    """
    CLI entrypoint.
    """
    parser = build_parser()

    args = parser.parse_args()

    launcher = args.launcher
    include_steam = launcher in ("all", "steam")
    needs_games = args.list_games or args.app_id or args.appid_from_name

    steam_path = (
        args.steam_root or get_steam_path() if args.steam_path or include_steam else args.steam_root
    )

    if (args.steam_path or (launcher == "steam" and needs_games)) and not steam_path:
        print_json(
            {"error": "Steam installation not found"},
            pretty=args.pretty,
        )
        return 1

    if include_steam and args.steam_root and steam_path and not steam_path.exists():
        print_json(
            {
                "error": "Steam root does not exist",
                "steam_path": str(steam_path),
            },
            pretty=args.pretty,
        )
        return 1

    games_cache: list[InstalledGame] | None = None

    if needs_games:
        if include_steam and not steam_path:
            warn("Steam installation not found", debug=args.debug)

        games_cache = build_installed_game_index(
            steam_root=steam_path,
            heroic_root=args.heroic_root,
            lutris_root=args.lutris_root,
            launcher=launcher,
            debug=args.debug,
        )

    output: dict[str, Any] = {
        "steam_path": str(steam_path) if steam_path else None,
    }

    if args.list_games:
        output["games"] = [game.to_json() for game in games_cache or []]

    if args.app_id:
        game = get_game_by_appid(
            games_cache or [],
            args.app_id,
        )

        output["game"] = game.to_json() if game else None

        if game:
            output["app_path"] = str(game.path) if game.path else None

    if args.appid_from_name:
        result = fuzzy_match_game(
            args.appid_from_name,
            games_cache or [],
        )

        match = result["match"]
        output["match"] = match.to_json() if match else None
        output["candidates"] = result["candidates"]
        output["score"] = result["score"]

    print_json(output, pretty=args.pretty)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
