from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.config import Config


class IsAdmin(BaseFilter):
    """Passes only for user IDs listed in Config.admin_ids."""

    def __init__(self, config: Config) -> None:
        self._admin_ids = config.admin_ids

    async def __call__(self, message: Message) -> bool:
        return (
            message.from_user is not None
            and message.from_user.id in self._admin_ids
        )