"""SQLite database helpers for progress tracking."""
import os
import json
import aiosqlite
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "/data/progress.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                module_id TEXT NOT NULL,
                lesson_slug TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                completed_at TEXT,
                notes TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                answers_json TEXT NOT NULL,
                attempted_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_lessons_module
            ON lessons(module_id)
        """)
        await db.commit()


async def mark_lesson_complete(lesson_id: str, module_id: str, lesson_slug: str):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO lessons (id, module_id, lesson_slug, completed, completed_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(id) DO UPDATE SET completed=1, completed_at=?
        """, (lesson_id, module_id, lesson_slug, now, now))
        await db.commit()


async def mark_lesson_incomplete(lesson_id: str, module_id: str, lesson_slug: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO lessons (id, module_id, lesson_slug, completed, completed_at)
            VALUES (?, ?, ?, 0, NULL)
            ON CONFLICT(id) DO UPDATE SET completed=0, completed_at=NULL
        """, (lesson_id, module_id, lesson_slug))
        await db.commit()


async def get_progress() -> dict:
    """Return {lesson_id: {completed, completed_at}} for all lessons."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM lessons")
        rows = await cursor.fetchall()
        return {row["id"]: dict(row) for row in rows}


async def get_module_progress(module_id: str) -> dict:
    """Return progress for a specific module."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM lessons WHERE module_id = ?", (module_id,)
        )
        rows = await cursor.fetchall()
        return {row["id"]: dict(row) for row in rows}


async def save_quiz_attempt(quiz_id: str, score: int, total: int, answers: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO quiz_attempts (quiz_id, score, total, answers_json, attempted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (quiz_id, score, total, json.dumps(answers), now))
        await db.commit()


async def get_quiz_best(quiz_id: str) -> dict | None:
    """Return the best quiz attempt."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM quiz_attempts
            WHERE quiz_id = ?
            ORDER BY score DESC, attempted_at DESC
            LIMIT 1
        """, (quiz_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
