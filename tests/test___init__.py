import game_install_finder


def test_version_attribute():
    assert hasattr(game_install_finder, "__version__")
