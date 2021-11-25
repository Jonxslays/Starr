import typing as t
from os import environ
from pathlib import Path

import hikari
import tanjun

from starr.db import Database
from starr.logging import Logger
from starr.models import GuildStore, StarrGuild




class StarrBot(hikari.GatewayBot):

    __slots__ = ("star", "db", "guilds", "log", "client")

    def __init__(self) -> None:
        super().__init__(
            token=environ["TOKEN"],
            intents=(
                hikari.Intents.GUILD_MESSAGE_REACTIONS |
                hikari.Intents.GUILD_MESSAGES |
                hikari.Intents.GUILD_MEMBERS |
                hikari.Intents.GUILDS
            )
        )

        self.star = "⭐"
        self.db = Database()
        self.guilds = GuildStore()
        self.log = Logger.setup()
        self.client = (
            tanjun.Client.from_gateway_bot(
                self,
                mention_prefix=True,
                declare_global_commands=int(environ.get("DEV", 0)) or True,
            )
            .set_prefix_getter(self.resolve_prefix)
            .load_modules(*Path("./starr/modules").glob("*.py"))
        )

        subscriptions: dict[
            t.Type[hikari.Event], t.Callable[[t.Any], t.Coroutine[t.Any, t.Any, None]]
        ] = {
            hikari.StartingEvent: self.on_starting,
            hikari.StartedEvent: self.on_started,
            hikari.StoppedEvent: self.on_stopped,
            hikari.GuildAvailableEvent: self.on_guild_available,
            hikari.GuildJoinEvent: self.on_guild_available,
        }

        for event, callback in subscriptions.items():
            self.subscribe(event, callback)

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        await self.db.connect()

    async def on_started(self, _: hikari.StartedEvent) -> None:
        if data := await self.db.rows("SELECT * FROM guilds;"):
            for guild in data:
                self.guilds.insert(StarrGuild(*guild))

    async def on_stopped(self, _: hikari.StoppingEvent) -> None:
        await self.db.close()

    async def on_guild_available(
        self,
        event: hikari.GuildAvailableEvent | hikari.GuildJoinEvent
    ) -> None:
        if event.guild_id not in self.guilds:
            guild = await StarrGuild.default_with_insert(self.db, event.guild_id)
            self.guilds.insert(guild)

    async def resolve_prefix(self, ctx: tanjun.MessageContext) -> tuple[str]:
        assert ctx.guild_id is not None

        if guild := self.guilds.get(ctx.guild_id):
            return (guild.prefix,)

        return ("$",)
