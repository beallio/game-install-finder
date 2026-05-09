from pathlib import Path

from game_install_finder.cli import (
    InstalledGame,
    build_heroic_index,
    build_parser,
    filter_games_by_launcher,
)


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


def test_help_documents_launcher_filter():
    help_text = build_parser().format_help()

    assert "--launcher LAUNCHER" in help_text
    assert "Filter installed games by launcher" in help_text


def test_filter_games_by_launcher_includes_matching_launcher(tmp_path):
    steam_game = InstalledGame(
        launcher="steam",
        appid="1",
        name="Steam Game",
        installdir="SteamGame",
        path=tmp_path / "SteamGame",
        exists=True,
        source=tmp_path / "appmanifest_1.acf",
    )
    heroic_game = InstalledGame(
        launcher="heroic",
        appid=None,
        name="Heroic Game",
        installdir=None,
        path=tmp_path / "HeroicGame",
        exists=True,
        source=tmp_path / "installed.json",
    )

    assert filter_games_by_launcher([steam_game, heroic_game], "steam") == [steam_game]
    assert filter_games_by_launcher([steam_game, heroic_game], "all") == [
        steam_game,
        heroic_game,
    ]


def test_filter_games_by_launcher_excludes_nonmatching_launcher(tmp_path):
    steam_game = InstalledGame(
        launcher="steam",
        appid="1",
        name="Steam Game",
        installdir="SteamGame",
        path=tmp_path / "SteamGame",
        exists=True,
        source=tmp_path / "appmanifest_1.acf",
    )

    assert filter_games_by_launcher([steam_game], "heroic") == []


def test_build_heroic_index_reads_installed_metadata(tmp_path):
    heroic_root = tmp_path / "heroic"
    install_path = tmp_path / "Heroic Game"
    install_path.mkdir()
    (heroic_root).mkdir()
    (heroic_root / "installed.json").write_text(
        """
{
  "ExampleApp": {
    "title": "Heroic Game",
    "install_path": "%s"
  }
}
"""
        % install_path,
        encoding="utf-8",
    )

    games = build_heroic_index(heroic_root)

    assert len(games) == 1
    assert games[0].launcher == "heroic"
    assert games[0].name == "Heroic Game"
    assert games[0].path == install_path
    assert games[0].exists is True
    assert games[0].source == heroic_root / "installed.json"


def test_build_heroic_index_missing_config_returns_empty_list(tmp_path):
    assert build_heroic_index(tmp_path / "missing") == []


def test_build_heroic_index_malformed_json_warns_under_debug(tmp_path, capsys):
    heroic_root = tmp_path / "heroic"
    heroic_root.mkdir()
    (heroic_root / "installed.json").write_text("{", encoding="utf-8")

    assert build_heroic_index(heroic_root, debug=True) == []

    captured = capsys.readouterr()

    assert "warning:" in captured.err
    assert "could not parse Heroic metadata" in captured.err
