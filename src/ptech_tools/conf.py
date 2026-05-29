from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings

ENV_PREFIX = "PTECH_TOOLS_EXPORT_DB_"

DEFAULT_EXPORT_DB_SETTINGS: dict[str, Any] = {
    "database_alias": "default",
    "output_dir": Path("backups"),
    "filename_template": "{database_alias}_{timestamp}.sql",
    "timestamp_format": "%Y%m%d_%H%M%S",
    "engine": "auto",
    "pg_dump_path": "pg_dump",
    "mysqldump_path": "mysqldump",
    "compress": False,
    "include_tables": (),
    "exclude_tables": (),
}

_SETTINGS_KEY_MAP = {
    "database_alias": "DATABASE_ALIAS",
    "output_dir": "OUTPUT_DIR",
    "filename_template": "FILENAME_TEMPLATE",
    "timestamp_format": "TIMESTAMP_FORMAT",
    "engine": "ENGINE",
    "pg_dump_path": "PG_DUMP_PATH",
    "mysqldump_path": "MYSQLDUMP_PATH",
    "compress": "COMPRESS",
    "include_tables": "INCLUDE_TABLES",
    "exclude_tables": "EXCLUDE_TABLES",
}


@dataclass(frozen=True, slots=True)
class ExportDBConfig:
    database_alias: str = "default"
    output_dir: Path = Path("backups")
    filename_template: str = "{database_alias}_{timestamp}.sql"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    engine: str = "auto"
    pg_dump_path: str = "pg_dump"
    mysqldump_path: str = "mysqldump"
    compress: bool = False
    include_tables: tuple[str, ...] = ()
    exclude_tables: tuple[str, ...] = ()


def load_export_db_config(overrides: Mapping[str, Any] | None = None) -> ExportDBConfig:
    raw = dict(DEFAULT_EXPORT_DB_SETTINGS)
    raw.update(_load_settings_overrides())
    raw.update(_load_env_overrides())

    if overrides:
        raw.update({key: value for key, value in overrides.items() if value is not None})

    return ExportDBConfig(
        database_alias=str(raw["database_alias"]),
        output_dir=_as_path(raw["output_dir"]),
        filename_template=str(raw["filename_template"]),
        timestamp_format=str(raw["timestamp_format"]),
        engine=str(raw["engine"]),
        pg_dump_path=str(raw["pg_dump_path"]),
        mysqldump_path=str(raw["mysqldump_path"]),
        compress=_as_bool(raw["compress"]),
        include_tables=_as_str_tuple(raw["include_tables"]),
        exclude_tables=_as_str_tuple(raw["exclude_tables"]),
    )


def _load_settings_overrides() -> dict[str, Any]:
    if not settings.configured:
        return {}

    tool_settings = getattr(settings, "PTECH_TOOLS", {})
    if not isinstance(tool_settings, Mapping):
        raise TypeError("settings.PTECH_TOOLS must be a mapping")

    export_db_settings = tool_settings.get("EXPORT_DB") or tool_settings.get("export_db") or {}
    if not isinstance(export_db_settings, Mapping):
        raise TypeError("settings.PTECH_TOOLS['EXPORT_DB'] must be a mapping")

    normalized: dict[str, Any] = {}
    for key, env_key in _SETTINGS_KEY_MAP.items():
        if key in export_db_settings:
            normalized[key] = export_db_settings[key]
        elif env_key in export_db_settings:
            normalized[key] = export_db_settings[env_key]
    return normalized


def _load_env_overrides() -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, env_key in _SETTINGS_KEY_MAP.items():
        value = os.getenv(f"{ENV_PREFIX}{env_key}")
        if value is not None:
            normalized[key] = value
    return normalized


def _as_path(value: Any) -> Path:
    if isinstance(value, Path):
        return value
    return Path(str(value)).expanduser()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError(f"Cannot interpret {value!r} as a boolean")


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = [piece.strip() for piece in value.split(",")]
    elif isinstance(value, Mapping):
        items = [str(item).strip() for item in value.values()]
    else:
        try:
            items = [str(item).strip() for item in value]
        except TypeError:
            items = [str(value).strip()]

    return tuple(item for item in items if item)
