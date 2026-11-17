from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class Config:
    token: str
    admin_ids: frozenset[int]


def load_config() -> Config:
    token = getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in environment")

    raw = getenv("ADMIN_IDS", "")
    admin_ids = frozenset(
        int(part) for part in raw.replace(" ", "").split(",") if part.isdigit()
    )
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is not set or contains no numeric IDs")

    return Config(token=token, admin_ids=admin_ids)