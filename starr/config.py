import logging
import typing
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler


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
