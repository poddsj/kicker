import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from bot.services.member_store import MemberStore

log = logging.getLogger(__name__)

BATCH_SIZE = 10
BATCH_PAUSE_SEC = 0.5

# Raised by Telegram when a ban/unban hits a basic (non-super) group.
# No point retrying every user — abort the whole run once.
_SUPERGROUP_ONLY_MARKER = "only in supergroup and channel chats"


class NotASupergroupError(RuntimeError):
    """Chat is a basic group; Bot API refuses to ban/kick there."""


async def kick_all(
    bot: Bot,
    chat_id: int,
    requester_id: int,
    bot_id: int,
    store: MemberStore,
) -> tuple[int, int]:
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
            try:
                ok, bad = await _process_batch(bot, chat_id, batch)
            except NotASupergroupError:
                raise
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
        result = await _kick_one(bot, chat_id, user_id)
        if result is True:
            ok += 1
        elif result is False:
            bad += 1
        else:  # "not supergroup" sentinel
            raise NotASupergroupError(
                f"chat {chat_id} is not a supergroup; Bot API cannot kick there"
            )
    return ok, bad


async def _kick_one(bot: Bot, chat_id: int, user_id: int) -> bool | None:
    """Return True on success, False on ordinary failure,
    None when the chat is a basic group (caller aborts)."""
    try:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id)
        return True
    except TelegramBadRequest as exc:
        if _SUPERGROUP_ONLY_MARKER in str(exc).lower():
            return None
        log.warning("kick failed chat=%s user=%s: %s", chat_id, user_id, exc)
        return False
    except TelegramAPIError as exc:
        log.warning("kick failed chat=%s user=%s: %s", chat_id, user_id, exc)
        return False