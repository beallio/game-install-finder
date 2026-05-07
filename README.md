# game-install-finder

Find local game install paths across PC game launchers. Currently supports Steam.

`game-install-finder` discovers local launcher libraries, enumerates installed games, and resolves
game install paths by launcher metadata. The first supported launcher is Steam; Heroic and Lutris
support are planned future additions. The tool only reads local files and does not call any game
store or launcher web API.

## Features

- Detects Steam on Windows, Linux, and macOS.
- Parses Steam `libraryfolders.vdf` with the `vdf` package instead of brittle string splitting.
- Includes games from primary and secondary Steam libraries.
- Reads Steam `appmanifest_*.acf` files to report appid, name, install directory, manifest path,
  and resolved local game path.
- Supports exact appid lookup and fuzzy installed-game name matching.
- Emits machine-readable JSON, with optional pretty printing.
- Keeps project virtualenvs and tool caches under `/tmp/game-install-finder` through `./run.sh`.

## Installation

Install project dependencies with `uv` through the repository wrapper:

```bash
./run.sh uv sync
```

The wrapper configures the project virtual environment and caches outside the repository:

```text
UV_PROJECT_ENVIRONMENT=/tmp/game-install-finder/.venv
XDG_CACHE_HOME=/tmp/game-install-finder/.cache
PYTHONPYCACHEPREFIX=/tmp/game-install-finder/__pycache__
TMPDIR=/tmp/game-install-finder
```

## Usage

Run the CLI from the repository root:

```bash
./run.sh uv run game-install-finder --help
```

List installed games:

```bash
./run.sh uv run game-install-finder --list-games --pretty
```

Print the detected Steam installation path:

```bash
./run.sh uv run game-install-finder --steam-path --pretty
```

Use an explicit Steam root instead of auto-detection:

```bash
./run.sh uv run game-install-finder --steam-root PATH --list-games --pretty
```

Find an installed Steam game by appid:

```bash
./run.sh uv run game-install-finder --app-id APPID --pretty
```

Fuzzy match an installed game name:

```bash
./run.sh uv run game-install-finder --appid-from-name NAME --pretty
```

Enable non-fatal parser and discovery warnings:

```bash
./run.sh uv run game-install-finder --list-games --debug --pretty
```

## CLI Options

```text
--steam-path            Return detected Steam installation path
--steam-root PATH       Use this Steam installation path instead of auto-detection
--list-games            Enumerate installed games
--app-id APPID          Lookup installed game by appid
--appid-from-name NAME  Fuzzy match installed game name to appid
--pretty                Pretty-print JSON output
--debug                 Print non-fatal parser/discovery warnings to stderr
```

## JSON output

All successful commands include `steam_path`. Additional fields depend on the selected lookup.

`--list-games` adds `games`, an array of records shaped like:

```json
{
  "appid": "730",
  "name": "Counter-Strike: Global Offensive",
  "installdir": "Counter-Strike Global Offensive",
  "path": "/home/user/.local/share/Steam/steamapps/common/Counter-Strike Global Offensive",
  "exists": true,
  "library": "/home/user/.local/share/Steam",
  "manifest": "/home/user/.local/share/Steam/steamapps/appmanifest_730.acf"
}
```

`--app-id APPID` adds:

```json
{
  "game": {
    "appid": "730",
    "name": "Counter-Strike: Global Offensive"
  },
  "app_path": "/home/user/.local/share/Steam/steamapps/common/Counter-Strike Global Offensive"
}
```

`--appid-from-name NAME` adds `match`, `candidates`, and `score`. If no confident fuzzy match is
found, `match` is `null` and `candidates` still lists the closest installed game names.

Errors are emitted as JSON and return a non-zero exit code:

```json
{
  "error": "Steam installation not found"
}
```

## Dependency requirements

- Python 3.12 or newer for this project.
- `uv` for dependency management, packaging, and command execution.
- Runtime dependency: `vdf`, used to parse Steam VDF and ACF metadata.
- Development tools: `pytest`, `pytest-cov`, `ruff`, and `ty`.

## Development

Run all project commands through `./run.sh`:

```bash
./run.sh uv run ruff check . --fix
./run.sh uv run ruff format .
./run.sh uv run ty check src/
./run.sh uv run pytest
```

Build the package with uv:

```bash
./run.sh uv build --no-sources
```

The repository follows the local agent protocol in `AGENTS.md`: plans live under `docs/plans/`,
tests must precede implementation changes, and generated caches must stay outside the repository.

## Publishing

PyPI publishing is configured for GitHub Actions Trusted Publishing. The PyPI project should be
configured with:

- Project name: `game-install-finder`
- Owner: `beallio`
- Repository name: `game-install-finder`
- Workflow name: `workflow.yml`
- Environment name: `pypi`

Release by pushing a version tag after the GitHub repository and PyPI Trusted Publisher are set up:

```bash
git tag -a v0.1.0 -m v0.1.0
git push origin v0.1.0
```

## License

MIT - See [LICENSE](LICENSE) for details.
