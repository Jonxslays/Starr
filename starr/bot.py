from os import environ
from pathlib import Path

import dotenv
import hikari
import tanjun

from starr.db import Database
from starr.logging import Logger
from starr.models import GuildStore, StarrGuild

dotenv.load_dotenv()


class StarrBot(hikari.GatewayBot):

    __slots__ = ("db", "guilds", "log", "client")

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

        subscriptions = {
            hikari.StartingEvent: self.on_starting,
            hikari.StartedEvent: self.on_started,
            hikari.StoppingEvent: self.on_stopping,
            hikari.GuildAvailableEvent: self.on_guild_available,
        }

        for event, callback in subscriptions.items():
            self.subscribe(event, callback)

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        await self.db.connect()

    async def on_started(self, _: hikari.StartedEvent) -> None:
        if data := await self.db.rows("SELECT GuildID, Prefix, StarChannel FROM guilds;"):
            for guild, prefix, channel in data:
                self.guilds.insert(StarrGuild(guild, prefix, channel))

    async def on_stopping(self, _: hikari.StoppingEvent) -> None:
        await self.db.close()

    async def on_guild_available(self, event: hikari.GuildAvailableEvent) -> None:
        if event.guild_id not in self.guilds:
            data = await self.db.row(
                "INSERT INTO guilds (GuildID) VALUES ($1) "
                "ON CONFLICT DO NOTHING "
                "RETURNING GuildID, Prefix, StarChannel;",
                event.guild_id
            )

            if data:
                self.guilds.insert(StarrGuild(*data))

    async def resolve_prefix(self, ctx: tanjun.MessageContext) -> tuple[str]:
        assert ctx.guild_id is not None
        guild = await self.guilds.get_or_insert(ctx.guild_id, self.db)
        return guild.prefix,
