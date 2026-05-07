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
        "Find local game install paths across PC game launchers",
        "Currently supports Steam",
        "Installation",
        "./run.sh uv sync",
        "Usage",
        "game-install-finder",
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


def test_project_declares_game_install_finder_metadata():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["name"] == "game-install-finder"
    assert project["description"] == (
        "Find local game install paths across PC game launchers. Currently supports Steam."
    )
    assert project["scripts"]["game-install-finder"] == "game_install_finder.cli:main"
    assert project["urls"]["Homepage"] == "https://github.com/beallio/game-install-finder"
    assert project["urls"]["Repository"] == "https://github.com/beallio/game-install-finder"
    assert project["urls"]["Issues"] == "https://github.com/beallio/game-install-finder/issues"


def test_cache_paths_use_game_install_finder_root():
    expected_root = "/tmp/game-install-finder"

    assert f"CACHE_ROOT={expected_root}" in Path(".protocol").read_text(encoding="utf-8")

    for file_path in (Path("run.sh"), Path(".envrc"), Path("pyproject.toml"), Path("README.md")):
        contents = file_path.read_text(encoding="utf-8")
        assert expected_root in contents
        assert "/tmp/game_path_finder" not in contents


def test_pypi_publish_workflow_uses_uv_and_trusted_publishing():
    workflow = Path(".github/workflows/workflow.yml").read_text(encoding="utf-8")

    required_phrases = [
        "environment: pypi",
        "id-token: write",
        "uv sync --locked --all-groups",
        "uv build --no-sources",
        "uv publish",
    ]

    for phrase in required_phrases:
        assert phrase in workflow
