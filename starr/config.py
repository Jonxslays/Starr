import logging
import typing
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler

from starr.db import Database


@dataclass(slots=True)
class StarrGuild:
    ident: int
    prefix: str
    star_channel: int | None = None


@dataclass(slots=True)
class GuildStore:
    data: dict[int, StarrGuild] = field(default_factory=dict)

    def get(self, ident: int) -> StarrGuild | None:
        return self.data.get(ident)

    def insert(self, ident: int, guild: StarrGuild) -> None:
        self.data[ident] = guild

    async def get_or_insert(self, ident: int, db: Database) -> StarrGuild:
        if not (starr_guild := self.get(ident)):
            guild, prefix, channel = await db.row(
                "INSERT INTO guilds (GuildID) VALUES ($1) "
                "ON CONFLICT DO NOTHING "
                "RETURNING GuildID, Prefix, StarChannel;",
                ident,
            )

            starr_guild = StarrGuild(guild, prefix, channel)
            self.insert(ident, starr_guild)

        return starr_guild

    def __contains__(self, ident: int) -> bool:
        return ident in self.data


@dataclass(slots=True)
class Logger:

    @classmethod
    def setup(cls) -> logging.Logger:
        log = logging.getLogger("root")
        log.setLevel(logging.INFO)

        rfh = RotatingFileHandler(
            "./starr/data/logs/main.log",
            maxBytes=512000,
            encoding="utf-8",
            backupCount=10,
        )

        ff = logging.Formatter(
            f"[%(asctime)s] %(levelname)s ||| %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        rfh.setFormatter(ff)
        log.addHandler(rfh)

        return log
