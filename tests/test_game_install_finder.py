from game_install_finder.cli import (
    build_parser,
    build_game_index,
    fuzzy_match_game,
    get_game_by_appid,
)


def test_build_game_index_reads_primary_and_secondary_libraries(tmp_path):
    steam_root = tmp_path / "steam"
    primary_apps = steam_root / "steamapps"
    primary_game = primary_apps / "common" / "PrimaryGame"
    secondary = tmp_path / "library"
    secondary_apps = secondary / "steamapps"
    secondary_game = secondary_apps / "common" / "SecondaryGame"

    primary_game.mkdir(parents=True)
    secondary_game.mkdir(parents=True)

    (primary_apps / "libraryfolders.vdf").write_text(
        f'''
"libraryfolders"
{{
    "1"
    {{
        "path" "{secondary}"
    }}
}}
''',
        encoding="utf-8",
    )
    (primary_apps / "appmanifest_100.acf").write_text(
        """
"AppState"
{
    "appid" "100"
    "name" "Primary Game"
    "installdir" "PrimaryGame"
}
""",
        encoding="utf-8",
    )
    (secondary_apps / "appmanifest_200.acf").write_text(
        """
"AppState"
{
    "appid" "200"
    "name" "Secondary Game"
    "installdir" "SecondaryGame"
}
""",
        encoding="utf-8",
    )

    games = build_game_index(steam_root)

    secondary_match = get_game_by_appid(games, "200")

    assert [game.appid for game in games] == ["100", "200"]
    assert [game.launcher for game in games] == ["steam", "steam"]
    assert all(game.exists for game in games)
    assert secondary_match is not None
    assert secondary_match.path == secondary_game
    assert secondary_match.source == secondary_apps / "appmanifest_200.acf"


def test_fuzzy_match_game_returns_best_installed_match(tmp_path):
    steam_root = tmp_path / "steam"
    steamapps = steam_root / "steamapps"
    (steamapps / "common" / "Counter-Strike Global Offensive").mkdir(parents=True)
    (steamapps / "appmanifest_730.acf").write_text(
        """
"AppState"
{
    "appid" "730"
    "name" "Counter-Strike: Global Offensive"
    "installdir" "Counter-Strike Global Offensive"
}
""",
        encoding="utf-8",
    )

    result = fuzzy_match_game("counter strike", build_game_index(steam_root))

    assert result["match"].appid == "730"
    assert result["match"].launcher == "steam"
    assert result["score"] >= 0.55


def test_help_uses_short_metavars_and_single_line_option_descriptions():
    help_text = build_parser().format_help()

    assert "--steam-root PATH       Use this Steam installation path" in help_text
    assert "--app-id APPID          Lookup installed game by appid" in help_text
    assert "--appid-from-name NAME  Fuzzy match installed game name" in help_text
    assert "APPID_FROM_NAME" not in help_text
