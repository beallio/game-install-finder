import subprocess
from pathlib import Path


def test_wrapper_diagnostic_is_on_stderr():
    """Verify that run.sh diagnostic output goes to stderr and leaves stdout clean."""
    repo_root = Path(__file__).resolve().parent.parent
    run_sh = repo_root / "run.sh"

    result = subprocess.run(
        [str(run_sh), "echo", "clean_stdout_content"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "clean_stdout_content" in result.stdout
    assert "Using environment:" not in result.stdout
    assert "Using environment:" in result.stderr


def test_cli_standalone_execution():
    """Verify that cli.py can be executed directly as a script (PEP 723 scenario)."""
    repo_root = Path(__file__).resolve().parent.parent
    cli_path = repo_root / "src" / "game_install_finder" / "cli.py"

    result = subprocess.run(
        ["uv", "run", str(cli_path), "--help"], cwd=repo_root, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "show this help message and exit" in result.stdout.lower()
    assert "ModuleNotFoundError" not in result.stderr
