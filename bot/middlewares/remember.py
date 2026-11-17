import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.services.member_store import MemberStore

log = logging.getLogger(__name__)

_GROUP_TYPES = frozenset({"group", "supergroup"})


class RememberMembersMiddleware(BaseMiddleware):
    """Persist every sender we see so /kickall has something to iterate.

    Bot API has no member-listing endpoint; this is the only way to build
    coverage of a chat's population over time.
    """

    def __init__(self, store: MemberStore) -> None:
        self._store = store

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        message = event.message or event.edited_message
        if (
            message is not None
            and message.from_user is not None
            and message.chat.type in _GROUP_TYPES
        ):
            try:
                await self._store.remember(
                    message.chat.id, message.from_user.id
                )
            except Exception as exc:
                # never let the cache failure break update dispatch
                log.warning("member cache write failed: %s", exc)
        return await handler(event, data)