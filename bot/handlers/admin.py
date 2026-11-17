from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated

from bot.filters.admin import IsAdmin
from bot.services.kicker import kick_all
from bot.services.member_store import MemberStore

router = Router(name="admin")
store = MemberStore()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Очистка чата.\n\n"
        "/kickall — выгнать всех (кроме админов, тебя и бота)\n"
        "/stats — сколько участников в базе"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    count = 0
    async for _ in store.iter_ids(message.chat.id):
        count += 1
    await message.answer(f"В базе: <b>{count}</b> участников.", parse_mode="HTML")


@router.message(Command("kickall"), IsAdmin())
async def cmd_kickall(message: Message, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("Команда работает только в группе.")
        return

    await message.answer("Чищу…")
    me = await bot.get_me()
    kicked, failed = await kick_all(bot, message.chat.id, message.from_user.id, me.id)
    await message.answer(
        f"Готово. Выгнано: <b>{kicked}</b>, ошибок: <b>{failed}</b>",
        parse_mode="HTML",
    )


# Cache any member we ever see (join events, messages handled by outer MW too)
@router.chat_member()
async def on_chat_member(update: ChatMemberUpdated) -> None:
    if update.new_chat_member.user.is_bot:
        return
    await store.remember(update.chat.id, update.new_chat_member.user.id)