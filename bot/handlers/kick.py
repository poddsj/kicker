import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message

from bot.filters.admin import IsAdmin
from bot.services.kicker import kick_all
from bot.services.member_store import MemberStore

log = logging.getLogger(__name__)

router = Router(name="kick")

_GROUP_TYPES = frozenset({"group", "supergroup"})


@router.message(Command("kickall"), IsAdmin())
async def cmd_kickall(
    message: Message,
    bot: Bot,
    store: MemberStore,
) -> None:
    if message.chat.type not in _GROUP_TYPES:
        await message.answer("Команда работает только в группе или супергруппе.")
        return

    await message.answer("Чищу…")

    me = await bot.get_me()
    kicked, failed = await kick_all(
        bot=bot,
        chat_id=message.chat.id,
        requester_id=message.from_user.id,
        bot_id=me.id,
        store=store,
    )

    await message.answer(
        f"Готово.\nВыгнано: <b>{kicked}</b>\nОшибок: <b>{failed}</b>",
        parse_mode="HTML",
    )


@router.chat_member()
async def on_chat_member(update: ChatMemberUpdated, store: MemberStore) -> None:
    """Cache new arrivals so a join is not lost before their first message."""
    user = update.new_chat_member.user
    if user.is_bot:
        return
    if update.chat.type not in _GROUP_TYPES:
        return
    try:
        await store.remember(update.chat.id, user.id)
    except Exception as exc:
        log.warning("chat_member cache write failed: %s", exc)