import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.services.member_store import MemberStore

log = logging.getLogger(__name__)

# Telegram soft limit is ~30 calls/sec globally. A ban+unban pair is 2 calls,
# so 10 users per 0.5s ~= 40 calls/sec bound — still under the ceiling with
# headroom for the rest of the bot's traffic.
BATCH_SIZE = 10
BATCH_PAUSE_SEC = 0.5


async def kick_all(
    bot: Bot,
    chat_id: int,
    requester_id: int,
    bot_id: int,
    store: MemberStore,
) -> tuple[int, int]:
    """Ban+unban every cached non-admin member so they're kicked out but
    remain re-invitable. Returns (kicked, failed)."""
    admins = {
        member.user.id
        for member in await bot.get_chat_administrators(chat_id)
    }

    kicked = 0
    failed = 0
    batch: list[int] = []

    async for user_id in store.iter_ids(chat_id):
        if user_id in admins or user_id == requester_id or user_id == bot_id:
            continue
        batch.append(user_id)
        if len(batch) >= BATCH_SIZE:
            ok, bad = await _process_batch(bot, chat_id, batch)
            kicked += ok
            failed += bad
            batch.clear()
            await asyncio.sleep(BATCH_PAUSE_SEC)

    if batch:
        ok, bad = await _process_batch(bot, chat_id, batch)
        kicked += ok
        failed += bad

    return kicked, failed


async def _process_batch(
    bot: Bot, chat_id: int, user_ids: list[int]
) -> tuple[int, int]:
    ok = 0
    bad = 0
    for user_id in user_ids:
        if await _kick_one(bot, chat_id, user_id):
            ok += 1
        else:
            bad += 1
    return ok, bad


async def _kick_one(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id)
        return True
    except TelegramAPIError as exc:
        log.warning("kick failed chat=%s user=%s: %s", chat_id, user_id, exc)
        return False