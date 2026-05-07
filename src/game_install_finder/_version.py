try:
    from importlib.metadata import version, PackageNotFoundError

    __version__ = version("game-install-finder")
except PackageNotFoundError:
    __version__ = "unknown"
