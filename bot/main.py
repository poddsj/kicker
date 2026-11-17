import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_config
from bot.handlers import common, kick
from bot.middlewares.remember import RememberMembersMiddleware
from bot.services.member_store import MemberStore


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)

    config = load_config()
    store = MemberStore()

    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Dependency injection: any handler can request these by name.
    dp["config"] = config
    dp["store"] = store

    # Cache senders BEFORE any handler runs.
    dp.update.outer_middleware(RememberMembersMiddleware(store))

    dp.include_router(common.router)
    dp.include_router(kick.router)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())