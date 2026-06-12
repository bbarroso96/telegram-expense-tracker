import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """App configuration, read from environment / .env.

    Only the Telegram bot needs BOT_TOKEN / ALLOWED_USER_IDS; the web API and
    seed scripts run fine without them, so those fields are optional.
    """

    db_path: str
    bot_token: str | None
    allowed_user_ids: set = field(default_factory=set)

    @classmethod
    def from_env(cls) -> "Config":
        raw_ids = os.environ.get("ALLOWED_USER_IDS", "")
        user_ids = {int(i.strip()) for i in raw_ids.split(",") if i.strip()}
        return cls(
            db_path=os.environ.get("DB_PATH", "data/expenses.db"),
            bot_token=os.environ.get("BOT_TOKEN"),
            allowed_user_ids=user_ids,
        )


config = Config.from_env()
