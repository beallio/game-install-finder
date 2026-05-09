from pathlib import Path

from game_install_finder.cli import InstalledGame


def test_installed_game_json_includes_launcher_and_string_paths(tmp_path):
    source = tmp_path / "source.json"
    game_path = tmp_path / "Game"
    library = tmp_path / "library"
    manifest = tmp_path / "appmanifest_1.acf"

    game = InstalledGame(
        launcher="steam",
        appid="1",
        name="Example",
        installdir="Example",
        path=game_path,
        exists=True,
        source=source,
        library=library,
        manifest=manifest,
    )

    assert game.to_json() == {
        "launcher": "steam",
        "appid": "1",
        "name": "Example",
        "installdir": "Example",
        "path": str(game_path),
        "exists": True,
        "source": str(source),
        "library": str(library),
        "manifest": str(manifest),
    }


def test_installed_game_allows_non_steam_records(tmp_path):
    game = InstalledGame(
        launcher="heroic",
        appid=None,
        name="Heroic Game",
        installdir=None,
        path=tmp_path / "Heroic Game",
        exists=False,
        source=Path("installed.json"),
    )

    assert game.launcher == "heroic"
    assert game.appid is None
    assert game.library is None
    assert game.manifest is None
