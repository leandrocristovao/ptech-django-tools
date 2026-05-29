class PtechToolsError(RuntimeError):
    """Base error for the package."""


class ConfigurationError(PtechToolsError):
    """Raised when the package settings are invalid or incomplete."""


class UnsupportedDatabaseEngineError(PtechToolsError):
    """Raised when the configured database engine cannot be exported."""

    def __init__(self, engine: str) -> None:
        super().__init__(f"Unsupported database engine: {engine}")
        self.engine = engine

