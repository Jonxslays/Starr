from os import environ

import dotenv
import hikari
import lightbulb

from starr.config import Logger, StarrGuild
from starr.db import AsyncPGDatabase

dotenv.load_dotenv()


async def prefix_getter(bot: lightbulb.BotApp, msg: hikari.Message) -> str:
    # TODO: get prefixes from db
    return "$"


app = lightbulb.BotApp(
    token=environ["TOKEN"],
    prefix=lightbulb.when_mentioned_or(prefix_getter),
    case_insensitive_prefix_commands=True,
    ignore_bots=True,
)


@app.listen(hikari.StartingEvent)
async def on_starting(_: hikari.StartingEvent) -> None:
    app.d.log = Logger.setup()

    app.d.db = AsyncPGDatabase()
    await app.d.db.connect()

    app.d.guilds = {}


@app.listen(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    if guilds_data :=  await app.d.db.rows("SELECT GuildID, Prefix, StarChannel FROM guilds;"):
        for guild, prefix, channel in guilds_data:
            app.d.guilds[guild] = StarrGuild(guild, prefix, channel)


@app.listen(hikari.GuildAvailableEvent)
async def on_guild_available(event: hikari.GuildAvailableEvent) -> None:
    if event.guild_id not in app.d.guilds:
        await app.d.db.execute(
            "INSERT INTO guilds (GuildID) VALUES ($1) ON CONFLICT DO NOTHING;", event.guild_id
        )


@app.listen(hikari.StoppingEvent)
async def on_stopping(_: hikari.StoppingEvent) -> None:
    await app.d.db.close()
