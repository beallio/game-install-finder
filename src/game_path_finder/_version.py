try:
    from importlib.metadata import version, PackageNotFoundError

    __version__ = version("game_path_finder")
except PackageNotFoundError:
    __version__ = "unknown"
