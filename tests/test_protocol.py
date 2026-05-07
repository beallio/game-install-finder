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
