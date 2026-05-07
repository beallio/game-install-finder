import tomllib
from pathlib import Path


def test_plans_directory():
    assert Path("docs/plans").exists()


def test_agents_file():
    assert Path("AGENTS.md").exists()


def test_no_gemini_specific_ignore_file():
    assert not Path(".geminiignore").exists()


def test_generated_python_caches_stay_outside_repository():
    generated_cache_paths = [
        path
        for root in (Path("src"), Path("tests"))
        for path in root.rglob("*")
        if path.name == "__pycache__" or path.suffix == ".pyc"
    ]

    assert generated_cache_paths == []


def test_readme_documents_tool_usage_and_dependencies():
    readme = Path("README.md").read_text(encoding="utf-8")

    required_phrases = [
        "Steam library and installed-game path discovery CLI",
        "Installation",
        "./run.sh uv sync",
        "Usage",
        "game-path-finder",
        "--steam-root PATH",
        "--list-games",
        "--app-id APPID",
        "--appid-from-name NAME",
        "JSON output",
        "Dependency requirements",
        "vdf",
    ]

    for phrase in required_phrases:
        assert phrase in readme


def test_project_declares_game_path_finder_console_script():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["game-path-finder"] == (
        "game_path_finder.game_path_finder:main"
    )
