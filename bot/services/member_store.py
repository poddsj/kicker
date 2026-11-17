import asyncio
import sqlite3
from typing import AsyncIterator


class MemberStore:
    """Persistent set of (chat_id, user_id) pairs the bot has ever seen.

    Uses stdlib sqlite3 with short-lived connections; each write/read
    runs in a worker thread via asyncio.to_thread so the event loop
    never blocks on disk I/O. No external dependencies.
    """

    def __init__(self, db_path: str = "members.db") -> None:
        self._db_path = db_path
        self._lock = asyncio.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS members ("
                "  chat_id INTEGER NOT NULL,"
                "  user_id INTEGER NOT NULL,"
                "  PRIMARY KEY (chat_id, user_id)"
                ")"
            )
            conn.commit()

    # ---- synchronous bodies, called from threads ----

    def _remember_sync(self, chat_id: int, user_id: int) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO members (chat_id, user_id) VALUES (?, ?)",
                (chat_id, user_id),
            )
            conn.commit()

    def _select_ids_sync(self, chat_id: int) -> list[int]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT user_id FROM members WHERE chat_id = ?", (chat_id,)
            ).fetchall()
        return [int(r[0]) for r in rows]

    def _count_sync(self, chat_id: int) -> int:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM members WHERE chat_id = ?", (chat_id,)
            ).fetchone()
        return int(row[0]) if row else 0

    # ---- async facade ----

    async def remember(self, chat_id: int, user_id: int) -> None:
        async with self._lock:
            await asyncio.to_thread(self._remember_sync, chat_id, user_id)

    async def iter_ids(self, chat_id: int) -> AsyncIterator[int]:
        # snapshot in a thread, then yield — avoids holding a cursor
        # across awaits and keeps the event loop free while fetching.
        ids = await asyncio.to_thread(self._select_ids_sync, chat_id)
        for uid in ids:
            yield uid

    async def count(self, chat_id: int) -> int:
        return await asyncio.to_thread(self._count_sync, chat_id)