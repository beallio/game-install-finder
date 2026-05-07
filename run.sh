#!/usr/bin/env bash
export UV_PROJECT_ENVIRONMENT=/tmp/game_path_finder/.venv
export XDG_CACHE_HOME=/tmp/game_path_finder/.cache
export PYTHONPYCACHEPREFIX=/tmp/game_path_finder/__pycache__
export TMPDIR=/tmp/game_path_finder
export PATH="/tmp/game_path_finder/.venv/bin:$PATH"

echo "Using environment: /tmp/game_path_finder/.venv"
exec "$@"
