import logging
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler


@dataclass
class StarrGuild:
    ident: int
    prefix: str
    star_channel: int | None = None


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
