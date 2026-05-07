#!/usr/bin/env bash
export UV_PROJECT_ENVIRONMENT=/tmp/game-install-finder/.venv
export XDG_CACHE_HOME=/tmp/game-install-finder/.cache
export PYTHONPYCACHEPREFIX=/tmp/game-install-finder/__pycache__
export TMPDIR=/tmp/game-install-finder
export PATH="/tmp/game-install-finder/.venv/bin:$PATH"

echo "Using environment: /tmp/game-install-finder/.venv"
exec "$@"
