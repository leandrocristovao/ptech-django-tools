from __future__ import annotations

import gzip
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from django.db import connections

from ptech_tools.conf import ExportDBConfig, load_export_db_config
from ptech_tools.exceptions import ConfigurationError, UnsupportedDatabaseEngineError

_ENGINE_ALIASES = {
    "postgres": "postgres",
    "postgresql": "postgres",
    "sqlite": "sqlite",
    "sqlite3": "sqlite",
    "mysql": "mysql",
}

_SQLITE_KEEP_ALWAYS = {
    "BEGIN TRANSACTION;",
    "COMMIT;",
    "PRAGMA FOREIGN_KEYS=OFF;",
}

_SQLITE_TABLE_PATTERNS = (
    re.compile(
        r'^(?:CREATE TABLE(?: IF NOT EXISTS)?|INSERT INTO|DELETE FROM|DROP TABLE(?: IF EXISTS)?)\s+(?:"(?P<quoted>[^"]+)"|(?P<bare>[^\s(]+))',
        re.IGNORECASE,
    ),
    re.compile(
        r'^(?:CREATE (?:UNIQUE )?INDEX\b.*?\bON|CREATE TRIGGER\b.*?\bON)\s+(?:"(?P<quoted>[^"]+)"|(?P<bare>[^\s(]+))',
        re.IGNORECASE,
    ),
)


class ConnectionLike(Protocol):
    settings_dict: dict[str, Any]

    def ensure_connection(self) -> None: ...

    @property
    def connection(self) -> Any: ...


class ExportDBService:
    def __init__(
        self,
        config: ExportDBConfig | None = None,
        *,
        connection: ConnectionLike | None = None,
        runner: Any | None = None,
        clock: Any | None = None,
    ) -> None:
        self.config = config or load_export_db_config()
        self._connection = connection
        self._runner = runner or subprocess.run
        self._clock = clock or datetime.now

    def build_target_path(self) -> Path:
        timestamp = self._clock().strftime(self.config.timestamp_format)
        filename = self.config.filename_template.format(
            database_alias=self.config.database_alias,
            timestamp=timestamp,
        )
        if self.config.compress and not str(filename).endswith(".gz"):
            filename = f"{filename}.gz"
        return self.config.output_dir / filename

    def resolve_backend(self) -> str:
        configured_engine = self._normalize_engine(self.config.engine)
        if configured_engine != "auto":
            return configured_engine

        engine_name = self.connection.settings_dict.get("ENGINE", "")
        if "sqlite3" in engine_name:
            return "sqlite"
        if "postgresql" in engine_name:
            return "postgres"
        if "mysql" in engine_name:
            return "mysql"
        raise UnsupportedDatabaseEngineError(engine_name or "unknown")

    def export(self) -> Path:
        target = self.build_target_path()
        target.parent.mkdir(parents=True, exist_ok=True)

        backend = self.resolve_backend()
        if backend == "sqlite":
            self._export_sqlite(target)
            return target

        self._export_external(backend, target)
        return target

    @property
    def connection(self) -> ConnectionLike:
        if self._connection is None:
            self._connection = connections[self.config.database_alias]
        return self._connection

    def _export_sqlite(self, target: Path) -> None:
        self.connection.ensure_connection()
        raw_connection = self.connection.connection
        if raw_connection is None:
            raise ConfigurationError("SQLite connection is not available")
        if not hasattr(raw_connection, "iterdump"):
            raise ConfigurationError("SQLite connection does not support iterdump()")

        if self.config.compress:
            handle_context = gzip.open(target, "wt", encoding="utf-8", newline="\n")
        else:
            handle_context = target.open("w", encoding="utf-8", newline="\n")

        with handle_context as handle:
            for statement in raw_connection.iterdump():
                if self._should_keep_sqlite_statement(statement):
                    handle.write(f"{statement}\n")

    def _export_external(self, backend: str, target: Path) -> None:
        command, env = self._build_external_command(backend)

        if self.config.compress:
            temp_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(mode="wb", delete=False, dir=target.parent) as temp_output:
                    temp_path = Path(temp_output.name)
                    self._runner(command, check=True, env=env, stdout=temp_output)

                assert temp_path is not None
                with temp_path.open("rb") as source, gzip.open(target, "wb") as destination:
                    shutil.copyfileobj(source, destination)
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
            return

        with target.open("wb") as output:
            self._runner(command, check=True, env=env, stdout=output)

    def _build_external_command(self, backend: str) -> tuple[list[str], dict[str, str]]:
        db_settings = self.connection.settings_dict
        database_name = db_settings.get("NAME")
        if not database_name:
            raise ConfigurationError("Database NAME is required")

        env = os.environ.copy()

        if backend == "postgres":
            command = [
                self.config.pg_dump_path,
                "--no-owner",
                "--no-acl",
                "--no-password",
                "-F",
                "p",
            ]
            if host := db_settings.get("HOST"):
                command.extend(["--host", str(host)])
            if port := db_settings.get("PORT"):
                command.extend(["--port", str(port)])
            if user := db_settings.get("USER"):
                command.extend(["--username", str(user)])
            if password := db_settings.get("PASSWORD"):
                env["PGPASSWORD"] = str(password)
            for table in self.config.include_tables:
                command.append(f"--table={table}")
            for table in self.config.exclude_tables:
                command.append(f"--exclude-table={table}")
            command.append(str(database_name))
            return command, env

        if backend == "mysql":
            command = [
                self.config.mysqldump_path,
                "--single-transaction",
                "--quick",
                "--skip-lock-tables",
                "--routines",
                "--triggers",
                "--events",
            ]
            if host := db_settings.get("HOST"):
                command.extend(["--host", str(host)])
            if port := db_settings.get("PORT"):
                command.extend(["--port", str(port)])
            if user := db_settings.get("USER"):
                command.extend(["--user", str(user)])
            if password := db_settings.get("PASSWORD"):
                env["MYSQL_PWD"] = str(password)
            for table in self.config.exclude_tables:
                command.append(f"--ignore-table={database_name}.{table}")
            command.append(str(database_name))
            command.extend(self.config.include_tables)
            return command, env

        raise UnsupportedDatabaseEngineError(backend)

    def _normalize_engine(self, engine: str) -> str:
        normalized = engine.lower().strip()
        if normalized == "auto":
            return normalized
        if normalized in _ENGINE_ALIASES:
            return _ENGINE_ALIASES[normalized]
        raise ConfigurationError(f"Unsupported engine override: {engine}")

    def _should_keep_sqlite_statement(self, statement: str) -> bool:
        normalized = statement.strip()
        if not normalized:
            return False

        upper = normalized.upper()
        if upper in _SQLITE_KEEP_ALWAYS or upper.startswith("PRAGMA "):
            return True

        table_name = self._sqlite_statement_table_name(normalized)
        if table_name is None or table_name == "sqlite_sequence":
            return True

        if self.config.include_tables and table_name not in self.config.include_tables:
            return False
        if table_name in self.config.exclude_tables:
            return False
        return True

    def _sqlite_statement_table_name(self, statement: str) -> str | None:
        for pattern in _SQLITE_TABLE_PATTERNS:
            match = pattern.match(statement)
            if match:
                return match.group("quoted") or match.group("bare")
        return None
