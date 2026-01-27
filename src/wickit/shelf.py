"""shelf - SQLite Database Utilities.

Shared SQLite database utilities for wickit products.
Provides base classes, connection management, and cloud sync helpers.

Features:
- SQLiteDatabase base class with connection pooling
- Automatic data directory management via hideaway
- Export to JSON for cloud sync
- Backup/restore utilities
- Migration support

Example:
    >>> from wickit import shelf
    >>> class JobDatabase(shelf.SQLiteDatabase):
    ...     def __init__(self):
    ...         super().__init__("jobforge", "jobs.db")
    ...     def get_all_jobs(self):
    ...         return self.query("SELECT * FROM jobs")
    >>> db = JobDatabase()
    >>> jobs = db.get_all_jobs()
"""

import json
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Generator, Optional, Type, TypeVar

from .hideaway import get_data_dir, ensure_data_dir

T = TypeVar("T")


class SQLiteDatabase:
    """Base class for SQLite databases with connection management and utilities.

    Attributes:
        product_name: Name of the product (e.g., "jobforge", "studya")
        db_name: Name of the database file (e.g., "jobs.db", "flashcards.db")
        db_path: Full path to the database file
    """

    def __init__(
        self,
        product_name: str,
        db_name: str,
        migrations: Optional[list[Callable[[sqlite3.Connection], None]]] = None,
    ):
        """Initialize database connection.

        Args:
            product_name: Name of the product (used for data directory)
            db_name: Name of the database file
            migrations: Optional list of migration functions to run
        """
        self.product_name = product_name
        self.db_name = db_name
        self._db_path = get_data_dir(product_name) / db_name
        self.migrations = migrations or []

        ensure_data_dir(product_name)
        self._init_db()

    @property
    def db_path(self) -> Path:
        """Get the full path to the database file."""
        return self._db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize the database schema. Override in subclasses."""
        pass

    def run_migrations(self) -> None:
        """Run any pending migrations."""
        with self.connect() as conn:
            for i, migration in enumerate(self.migrations, start=1):
                try:
                    migration(conn)
                except sqlite3.OperationalError:
                    pass

    def execute(
        self, query: str, params: tuple = ()
    ) -> sqlite3.Cursor:
        """Execute a query and return cursor."""
        with self.connect() as conn:
            return conn.execute(query, params)

    def query(
        self, query: str, params: tuple = ()
    ) -> list[sqlite3.Row]:
        """Execute a query and return all rows."""
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def query_one(
        self, query: str, params: tuple = ()
    ) -> Optional[sqlite3.Row]:
        """Execute a query and return first row."""
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()

    def insert(
        self, query: str, params: tuple = ()
    ) -> int:
        """Execute an insert and return rowid."""
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid

    def count(self, table: str, where: str = "1=1", params: tuple = ()) -> int:
        """Count rows in a table."""
        with self.connect() as conn:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {where}", params
            )
            return cursor.fetchone()[0]

    def exists(self, table: str, where: str = "1=1", params: tuple = ()) -> bool:
        """Check if any row exists."""
        return self.count(table, where, params) > 0

    def vacuum(self) -> None:
        """Optimize the database."""
        with self.connect() as conn:
            conn.execute("VACUUM")

    def backup(self, backup_path: Optional[Path] = None) -> Path:
        """Create a backup of the database.

        Args:
            backup_path: Optional path for backup. If not provided,
                        creates timestamped backup in data directory.

        Returns:
            Path to the backup file.
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self._db_path.parent / f"{self.db_name}.backup_{timestamp}.db"

        with self.connect() as conn:
            backup_conn = sqlite3.connect(str(backup_path))
            try:
                conn.backup(backup_conn)
            finally:
                backup_conn.close()

        return backup_path

    def export_to_json(
        self,
        tables: Optional[list[str]] = None,
        json_path: Optional[Path] = None,
    ) -> Path:
        """Export database to JSON for cloud sync.

        Args:
            tables: Optional list of tables to export. Exports all if None.
            json_path: Optional path for JSON file.

        Returns:
            Path to the JSON file.
        """
        if json_path is None:
            json_path = self._db_path.parent / f"{self.db_name}.json"

        data: dict[str, Any] = {
            "exported_at": datetime.now().isoformat(),
            "product": self.product_name,
            "database": self.db_name,
            "tables": {},
        }

        with self.connect() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            all_tables = [row[0] for row in cursor.fetchall()]

            tables_to_export = tables or all_tables
            for table in tables_to_export:
                if table in all_tables:
                    cursor = conn.execute(f"SELECT * FROM {table}")
                    columns = [desc[0] for desc in cursor.description]
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    data["tables"][table] = rows

        json_path.write_text(json.dumps(data, indent=2, default=str))
        return json_path

    @classmethod
    def import_from_json(
        cls,
        json_path: Path,
        product_name: str,
        db_name: str,
        clear_existing: bool = True,
    ) -> "SQLiteDatabase":
        """Import data from JSON file.

        Args:
            json_path: Path to JSON file
            product_name: Name of the product
            db_name: Name of the database
            clear_existing: Whether to clear existing data first

        Returns:
            New SQLiteDatabase instance with imported data
        """
        data = json.loads(json_path.read_text())

        db = cls(product_name, db_name)

        with db.connect() as conn:
            for table_name, rows in data.get("tables", {}).items():
                if clear_existing:
                    conn.execute(f"DELETE FROM {table_name}")

                if rows:
                    for row in rows:
                        columns = list(row.keys())
                        placeholders = ", ".join(["?"] * len(columns))
                        values = [row[col] for col in columns]
                        conn.execute(
                            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                            values,
                        )

        return db

    def get_table_names(self) -> list[str]:
        """Get list of all table names."""
        with self.connect() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_table_info(self, table: str) -> list[dict]:
        """Get column info for a table."""
        with self.connect() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            return [{"name": row[1], "type": row[2], "pk": row[5]} for row in cursor.fetchall()]

    def close(self) -> None:
        """Close all connections and vacuum."""
        self.vacuum()


def get_db_path(product_name: str, db_name: str) -> Path:
    """Get the path to a database file.

    Args:
        product_name: Name of the product
        db_name: Name of the database file

    Returns:
        Path to the database file
    """
    return get_data_dir(product_name) / db_name


def export_database(
    product_name: str,
    db_name: str,
    output_path: Optional[Path] = None,
) -> Path:
    """Convenience function to export a database to JSON.

    Args:
        product_name: Name of the product
        db_name: Name of the database file
        output_path: Optional output path

    Returns:
        Path to the exported JSON file
    """
    db_class = type("TempDB", (SQLiteDatabase,), {"_init_db": lambda self: None})
    temp_db = db_class(product_name, db_name)
    return temp_db.export_to_json(json_path=output_path)


def list_databases(product_name: Optional[str] = None) -> dict[str, list[str]]:
    """List all databases for a product or all products.

    Args:
        product_name: Optional product name. Lists all if None.

    Returns:
        Dict mapping product names to list of database files
    """
    result: dict[str, list[str]] = {}

    if product_name:
        data_dir = get_data_dir(product_name)
        if data_dir.exists():
            result[product_name] = [
                f.name for f in data_dir.glob("*.db") if f.is_file()
            ]
    else:
        for product in ["jobforge", "studya", "cv-studio", "aixam"]:
            data_dir = get_data_dir(product)
            if data_dir.exists():
                dbs = [f.name for f in data_dir.glob("*.db") if f.is_file()]
                if dbs:
                    result[product] = dbs

    return result


__all__ = [
    "SQLiteDatabase",
    "get_db_path",
    "export_database",
    "list_databases",
]
