import asyncio

import aiosqlite


class MemberStore:
    """Persistent set of (chat_id, user_id) pairs the bot has ever seen.

    Telegram Bot API does not expose a method to enumerate chat members,
    so we accumulate IDs via an outer middleware on every message and via
    the chat_member update handler on joins. /kickall iterates this table.
    """

    def __init__(self, db_path: str = "members.db") -> None:
        self._db_path = db_path
        self._lock = asyncio.Lock()

    async def _connect(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self._db_path)
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS members ("
            "  chat_id INTEGER NOT NULL,"
            "  user_id INTEGER NOT NULL,"
            "  PRIMARY KEY (chat_id, user_id)"
            ")"
        )
        await conn.commit()
        return conn

    async def remember(self, chat_id: int, user_id: int) -> None:
        async with self._lock:
            conn = await self._connect()
            try:
                await conn.execute(
                    "INSERT OR IGNORE INTO members (chat_id, user_id) "
                    "VALUES (?, ?)",
                    (chat_id, user_id),
                )
                await conn.commit()
            finally:
                await conn.close()

    async def iter_ids(self, chat_id: int):
        conn = await self._connect()
        try:
            async with conn.execute(
                "SELECT user_id FROM members WHERE chat_id = ?", (chat_id,)
            ) as cursor:
                async for (uid,) in cursor:
                    yield uid
        finally:
            await conn.close()

    async def count(self, chat_id: int) -> int:
        conn = await self._connect()
        try:
            async with conn.execute(
                "SELECT COUNT(*) FROM members WHERE chat_id = ?", (chat_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row else 0
        finally:
            await conn.close()