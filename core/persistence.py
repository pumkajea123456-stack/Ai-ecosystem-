"""Durable local persistence for tasks and audit events.

SQLite is the zero-service development backend. Production deployments should
use PostgreSQL with equivalent schema, migrations, backups, and access controls.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class CoreStore:
    def __init__(self, database_path: str = "data/autonomous_core.db"):
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        if self.database_path != ":memory:":
            connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self):
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    action TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'created',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    action TEXT NOT NULL,
                    allowed INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    result_json TEXT,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                );
                CREATE INDEX IF NOT EXISTS idx_audit_task_id
                    ON audit_events(task_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status
                    ON tasks(status);
            """)

    def save_task(self, task: Any, status: str = "created") -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO tasks
                   (task_id, agent, action, risk, parameters_json, status)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(task_id) DO UPDATE SET
                     agent=excluded.agent, action=excluded.action,
                     risk=excluded.risk, parameters_json=excluded.parameters_json,
                     status=excluded.status""",
                (task.task_id, task.agent, task.action, task.risk,
                 json.dumps(task.parameters, ensure_ascii=False, default=str), status),
            )

    def update_task_status(self, task_id: str, status: str) -> None:
        with self._connect() as db:
            cursor = db.execute(
                "UPDATE tasks SET status=? WHERE task_id=?", (status, task_id)
            )
            if cursor.rowcount == 0:
                raise KeyError(f"unknown task_id: {task_id}")

    def record_audit(self, event: dict[str, Any]) -> int:
        with self._connect() as db:
            cursor = db.execute(
                """INSERT INTO audit_events
                   (timestamp, task_id, agent, action, allowed, reason, result_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (event["timestamp"], event["task_id"], event["agent"],
                 event["action"], int(event["allowed"]), event["reason"],
                 json.dumps(event.get("result"), ensure_ascii=False, default=str)),
            )
            return int(cursor.lastrowid)

    def list_tasks(self, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["parameters"] = json.loads(item.pop("parameters_json"))
            result.append(item)
        return result

    def list_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["allowed"] = bool(item["allowed"])
            item["result"] = json.loads(item.pop("result_json") or "null")
            result.append(item)
        return result
