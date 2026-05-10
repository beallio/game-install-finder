from pathlib import Path
import json
import sqlite3

from game_install_finder.cli import (
    InstalledGame,
    build_heroic_index,
    build_installed_game_index,
    build_lutris_index,
    build_parser,
    filter_games_by_launcher,
    fuzzy_match_game,
    get_game_by_appid,
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

    assert "Steam, Heroic, and Lutris" in help_text
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


def test_build_heroic_index_reads_sideload_games_array_with_absolute_folder_name(tmp_path):
    heroic_root = tmp_path / "heroic"
    install_path = tmp_path / "X-Men Origins Wolverine"
    metadata_file = heroic_root / "sideload_apps" / "library.json"
    install_path.mkdir()
    metadata_file.parent.mkdir(parents=True)
    metadata_file.write_text(
        json.dumps(
            {
                "games": [
                    {
                        "app_name": "wolverine",
                        "title": "X-Men Origins Wolverine",
                        "folder_name": str(install_path),
                        "is_installed": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    games = build_heroic_index(heroic_root)

    assert len(games) == 1
    assert games[0].launcher == "heroic"
    assert games[0].appid == "wolverine"
    assert games[0].name == "X-Men Origins Wolverine"
    assert games[0].path == install_path
    assert games[0].exists is True
    assert games[0].source == metadata_file


def test_build_heroic_index_resolves_relative_sideload_folder_from_default_path(tmp_path):
    heroic_root = tmp_path / "heroic"
    default_install_path = tmp_path / "Heroic Games"
    install_path = default_install_path / "Deadpool"
    metadata_file = heroic_root / "sideload_apps" / "library.json"
    install_path.mkdir(parents=True)
    metadata_file.parent.mkdir(parents=True)
    metadata_file.write_text(
        json.dumps(
            {
                "defaultSettings": {"defaultInstallPath": str(default_install_path)},
                "games": [
                    {
                        "app_name": "deadpool",
                        "title": "Deadpool",
                        "folder_name": "Deadpool",
                        "is_installed": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    games = build_heroic_index(heroic_root)

    assert len(games) == 1
    assert games[0].appid == "deadpool"
    assert games[0].name == "Deadpool"
    assert games[0].path == install_path


def test_build_heroic_index_falls_back_to_install_executable_parent(tmp_path):
    heroic_root = tmp_path / "heroic"
    install_path = tmp_path / "Transformers Devastation"
    executable_path = install_path / "Transformers.exe"
    metadata_file = heroic_root / "sideload_apps" / "library.json"
    install_path.mkdir()
    executable_path.touch()
    metadata_file.parent.mkdir(parents=True)
    metadata_file.write_text(
        json.dumps(
            {
                "games": [
                    {
                        "app_name": "transformers-devastation",
                        "title": "Transformers Devastation",
                        "is_installed": True,
                        "install": {"executable": str(executable_path)},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    games = build_heroic_index(heroic_root)

    assert len(games) == 1
    assert games[0].appid == "transformers-devastation"
    assert games[0].name == "Transformers Devastation"
    assert games[0].path == install_path


def test_build_heroic_index_excludes_uninstalled_or_missing_sideload_records(tmp_path):
    heroic_root = tmp_path / "heroic"
    installed_path = tmp_path / "Installed Sideload"
    uninstalled_path = tmp_path / "Uninstalled Sideload"
    missing_path = tmp_path / "Missing Sideload"
    metadata_file = heroic_root / "sideload_apps" / "library.json"
    installed_path.mkdir()
    uninstalled_path.mkdir()
    metadata_file.parent.mkdir(parents=True)
    metadata_file.write_text(
        json.dumps(
            {
                "games": [
                    {
                        "title": "Installed Sideload",
                        "folder_name": str(installed_path),
                        "is_installed": True,
                    },
                    {
                        "title": "Missing Sideload",
                        "folder_name": str(missing_path),
                        "is_installed": True,
                    },
                    {
                        "title": "Uninstalled Sideload",
                        "folder_name": str(uninstalled_path),
                        "is_installed": False,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    games = build_heroic_index(heroic_root)

    assert [game.name for game in games] == ["Installed Sideload"]
    assert games[0].path == installed_path


def test_build_heroic_index_reads_store_cache_library_metadata(tmp_path):
    heroic_root = tmp_path / "heroic"
    install_path = tmp_path / "Store Cache Game"
    metadata_file = heroic_root / "store_cache" / "legendary_library.json"
    install_path.mkdir()
    metadata_file.parent.mkdir(parents=True)
    metadata_file.write_text(
        json.dumps(
            {
                "store-cache-game": {
                    "app_name": "store-cache-game",
                    "title": "Store Cache Game",
                    "install_path": str(install_path),
                    "is_installed": True,
                }
            }
        ),
        encoding="utf-8",
    )

    games = build_heroic_index(heroic_root)

    assert len(games) == 1
    assert games[0].appid == "store-cache-game"
    assert games[0].name == "Store Cache Game"
    assert games[0].path == install_path
    assert games[0].source == metadata_file


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


def test_build_lutris_index_reads_pga_database(tmp_path):
    lutris_root = tmp_path / "lutris"
    install_path = tmp_path / "lutris-game"
    install_path.mkdir()
    lutris_root.mkdir()

    connection = sqlite3.connect(lutris_root / "pga.db")
    connection.execute(
        "create table games (id integer, name text, installed integer, directory text)"
    )
    connection.execute(
        "insert into games (id, name, installed, directory) values (?, ?, ?, ?)",
        (7, "Lutris Game", 1, str(install_path)),
    )
    connection.commit()
    connection.close()

    games = build_lutris_index(lutris_root)

    assert len(games) == 1
    assert games[0].launcher == "lutris"
    assert games[0].name == "Lutris Game"
    assert games[0].path == install_path
    assert games[0].exists is True
    assert games[0].source == lutris_root / "pga.db"


def test_build_lutris_index_missing_data_root_returns_empty_list(tmp_path):
    assert build_lutris_index(tmp_path / "missing") == []


def test_build_lutris_index_bad_schema_warns_under_debug(tmp_path, capsys):
    lutris_root = tmp_path / "lutris"
    lutris_root.mkdir()

    connection = sqlite3.connect(lutris_root / "pga.db")
    connection.execute("create table games (title text)")
    connection.commit()
    connection.close()

    assert build_lutris_index(lutris_root, debug=True) == []

    captured = capsys.readouterr()

    assert "warning:" in captured.err
    assert "could not read Lutris metadata" in captured.err


def test_build_installed_game_index_combines_steam_heroic_and_lutris(tmp_path):
    steam_root = _write_steam_fixture(tmp_path, "100", "Steam Game", "SteamGame")
    heroic_root = _write_heroic_fixture(tmp_path, "Heroic Game")
    lutris_root = _write_lutris_fixture(tmp_path, "Lutris Game")

    games = build_installed_game_index(
        steam_root=steam_root,
        heroic_root=heroic_root,
        lutris_root=lutris_root,
        launcher="all",
    )

    assert [(game.launcher, game.name) for game in games] == [
        ("heroic", "Heroic Game"),
        ("lutris", "Lutris Game"),
        ("steam", "Steam Game"),
    ]


def test_fuzzy_match_game_returns_heroic_match_from_combined_index(tmp_path):
    games = build_installed_game_index(
        steam_root=_write_steam_fixture(tmp_path, "100", "Steam Game", "SteamGame"),
        heroic_root=_write_heroic_fixture(tmp_path, "Heroic Quest"),
        lutris_root=_write_lutris_fixture(tmp_path, "Lutris Game"),
        launcher="all",
    )

    result = fuzzy_match_game("heroic quest", games)

    assert result["match"].launcher == "heroic"
    assert result["match"].name == "Heroic Quest"


def test_fuzzy_match_game_returns_lutris_match_from_combined_index(tmp_path):
    games = build_installed_game_index(
        steam_root=_write_steam_fixture(tmp_path, "100", "Steam Game", "SteamGame"),
        heroic_root=_write_heroic_fixture(tmp_path, "Heroic Game"),
        lutris_root=_write_lutris_fixture(tmp_path, "Lutris Quest"),
        launcher="all",
    )

    result = fuzzy_match_game("lutris quest", games)

    assert result["match"].launcher == "lutris"
    assert result["match"].name == "Lutris Quest"


def test_build_installed_game_index_launcher_filter_narrows_fuzzy_results(tmp_path):
    steam_root = _write_steam_fixture(tmp_path, "100", "Shared Name Steam", "SharedSteam")
    heroic_root = _write_heroic_fixture(tmp_path, "Shared Name Heroic")
    lutris_root = _write_lutris_fixture(tmp_path, "Shared Name Lutris")

    heroic_games = build_installed_game_index(
        steam_root=steam_root,
        heroic_root=heroic_root,
        lutris_root=lutris_root,
        launcher="heroic",
    )
    lutris_games = build_installed_game_index(
        steam_root=steam_root,
        heroic_root=heroic_root,
        lutris_root=lutris_root,
        launcher="lutris",
    )

    assert fuzzy_match_game("shared name", heroic_games)["match"].launcher == "heroic"
    assert fuzzy_match_game("shared name", lutris_games)["match"].launcher == "lutris"


def test_get_game_by_appid_ignores_non_steam_records(tmp_path):
    heroic_game = InstalledGame(
        launcher="heroic",
        appid="100",
        name="Heroic Game",
        installdir=None,
        path=tmp_path / "HeroicGame",
        exists=True,
        source=tmp_path / "installed.json",
    )

    assert get_game_by_appid([heroic_game], "100") is None


def _write_steam_fixture(tmp_path, appid, name, installdir):
    steam_root = tmp_path / f"steam-{appid}"
    steamapps = steam_root / "steamapps"
    (steamapps / "common" / installdir).mkdir(parents=True)
    (steamapps / f"appmanifest_{appid}.acf").write_text(
        f'''
"AppState"
{{
    "appid" "{appid}"
    "name" "{name}"
    "installdir" "{installdir}"
}}
''',
        encoding="utf-8",
    )
    return steam_root


def _write_heroic_fixture(tmp_path, name):
    heroic_root = tmp_path / f"heroic-{name.replace(' ', '-').lower()}"
    install_path = tmp_path / f"{name.replace(' ', '-')}-install"
    heroic_root.mkdir()
    install_path.mkdir()
    (heroic_root / "installed.json").write_text(
        json_for_heroic_game(name, install_path),
        encoding="utf-8",
    )
    return heroic_root


def _write_lutris_fixture(tmp_path, name):
    lutris_root = tmp_path / f"lutris-{name.replace(' ', '-').lower()}"
    install_path = tmp_path / f"{name.replace(' ', '-')}-install"
    lutris_root.mkdir()
    install_path.mkdir()
    connection = sqlite3.connect(lutris_root / "pga.db")
    connection.execute(
        "create table games (id integer, name text, installed integer, directory text)"
    )
    connection.execute(
        "insert into games (id, name, installed, directory) values (?, ?, ?, ?)",
        (7, name, 1, str(install_path)),
    )
    connection.commit()
    connection.close()
    return lutris_root


def json_for_heroic_game(name, install_path):
    return """
{
  "ExampleApp": {
    "title": "%s",
    "install_path": "%s"
  }
}
""" % (name, install_path)
