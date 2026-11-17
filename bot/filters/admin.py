from os import getenv

from aiogram.filters import BaseFilter
from aiogram.types import Message


def _load_admin_ids() -> frozenset[int]:
    """Read ADMIN_IDS directly so the filter works at import time,
    before Config/DI exist. Same parsing as Config.load_config."""
    raw = getenv("ADMIN_IDS", "")
    ids = frozenset(
        int(part) for part in raw.replace(" ", "").split(",") if part.isdigit()
    )
    if not ids:
        raise RuntimeError("ADMIN_IDS is not set or contains no numeric IDs")
    return ids


class IsAdmin(BaseFilter):
    """Passes only for user IDs listed in ADMIN_IDS env var.

    No constructor args: filters are instantiated at decoration time,
    before load_config()/Dispatcher DI run.
    """

    def __init__(self) -> None:
        self._admin_ids = _load_admin_ids()

    async def __call__(self, message: Message) -> bool:
        return (
            message.from_user is not None
            and message.from_user.id in self._admin_ids
        )