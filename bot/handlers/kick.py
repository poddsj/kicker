import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message

from bot.filters.admin import IsAdmin
from bot.services.kicker import kick_all
from bot.services.member_store import MemberStore

log = logging.getLogger(__name__)

router = Router(name="kick")

_SUPERGROUP_ONLY_MSG = (
    "⚠️ Это обычная группа. Telegram Bot API не даёт ботам "
    "выгонять участников из basic group — только из супергрупп.\n\n"
    "Как перевести: настройки чата → «Тип чата» → "
    "«Перевести в супергруппу» (или добавь чат в любую папку / "
    "выдай право «Закреплять сообщения» — Telegram сам мигрирует).\n"
    "После миграции — повтори /kickall."
)


@router.message(Command("kickall"), IsAdmin())
async def cmd_kickall(
    message: Message,
    bot: Bot,
    store: MemberStore,
) -> None:
    if message.chat.type != "supergroup":
        await message.answer(_SUPERGROUP_ONLY_MSG)
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
    user = update.new_chat_member.user
    if user.is_bot:
        return
    if update.chat.type != "supergroup":
        return
    try:
        await store.remember(update.chat.id, user.id)
    except Exception as exc:
        log.warning("chat_member cache write failed: %s", exc)