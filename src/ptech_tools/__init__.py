from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ptech-tools")
except PackageNotFoundError:  # pragma: no cover - fallback for local source checkouts
    __version__ = "0.1.0"

