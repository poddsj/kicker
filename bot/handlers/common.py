from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.member_store import MemberStore

router = Router(name="common")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Добро пожаловать в <b>ChessIt</b>!\n\n"
        "Введите /play и @username человека с которым хотите сыграть!\n"
        "Приятной игры.",
        parse_mode="HTML",
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, store: MemberStore) -> None:
    total = await store.count(message.chat.id)
    await message.answer(
        f"В базе для этого чата: <b>{total}</b> участников.",
        parse_mode="HTML",
    )