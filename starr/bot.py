from os import environ

import dotenv
import hikari
import tanjun

from starr.config import GuildStore, Logger, StarrGuild
from starr.db import Database

dotenv.load_dotenv()


class StarrBot(hikari.GatewayBot):

    __slots__ = ("db", "guilds", "log", "client")

    def __init__(self) -> None:
        self.db = Database()
        self.guilds = GuildStore()
        self.log = Logger.setup()

        super().__init__(
            token=environ["TOKEN"],
            intents=hikari.Intents.GUILD_MESSAGES | hikari.Intents.GUILD_MEMBERS,
        )

        self.client = tanjun.Client.from_gateway_bot(
            self,
            mention_prefix=True,
            declare_global_commands=int(environ.get("DEV", 0)) or False,
        ).set_prefix_getter(self.resolve_prefix)

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        await self.db.connect()

    async def on_started(self, _: hikari.StartedEvent) -> None:
        if guilds_data := await self.db.rows("SELECT GuildID, Prefix, StarChannel FROM guilds;"):
            for guild, prefix, channel in guilds_data:
                self.guilds.insert(guild, StarrGuild(guild, prefix, channel))

    async def on_stopping(self, _: hikari.StoppingEvent) -> None:
        await self.db.close()

    async def on_guild_available(self, event: hikari.GuildAvailableEvent) -> None:
        if event.guild_id not in self.guilds:
            await self.db.execute(
                "INSERT INTO guilds (GuildID) VALUES ($1) ON CONFLICT DO NOTHING;", event.guild_id
            )

    async def resolve_prefix(self, ctx: tanjun.MessageContext) -> tuple[str]:
        # TODO: get prefixes from db
        return "$",
