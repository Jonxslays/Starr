import typing as t
from os import environ
from pathlib import Path

import hikari
import tanjun

from starr.db import Database
from starr.models import StarrGuild

SubscriptionsT = dict[t.Type[hikari.Event], t.Callable[...,  t.Coroutine[t.Any, t.Any, None]]]


class StarrBot(hikari.GatewayBot):

    __slots__ = ("star", "db", "guilds", "log", "client")

    def __init__(self) -> None:
        super().__init__(
            token=environ["TOKEN"],
            intents=hikari.Intents.ALL,
        )

        self.star = "\u2B50"
        self.db = Database()
        self.guilds: dict[int, StarrGuild] = {}
        self.client = (
            tanjun.Client.from_gateway_bot(
                self,
                mention_prefix=True,
                declare_global_commands=int(environ.get("DEV", environ["PROD"])),
            )
            .set_prefix_getter(self.resolve_prefix)
            .load_modules(*Path("./starr/modules").glob("[!_]*.py"))
        )

        subscriptions: SubscriptionsT = {
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
                obj = StarrGuild(*guild)
                self.guilds[obj.guild_id] = obj

    async def on_stopped(self, _: hikari.StoppingEvent) -> None:
        await self.db.close()

    async def on_guild_available(
        self, event: hikari.GuildAvailableEvent | hikari.GuildJoinEvent
    ) -> None:
        if event.guild_id not in self.guilds:
            guild = await StarrGuild.default_with_insert(self.db, event.guild_id)
            self.guilds[guild.guild_id] = guild

    async def resolve_prefix(self, ctx: tanjun.context.MessageContext) -> tuple[str]:
        assert ctx.guild_id is not None

        if guild := self.guilds.get(ctx.guild_id):
            return (guild.prefix,)

        return ("$",)
