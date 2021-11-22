import hikari
import tanjun

from starr.bot import StarrBot
from starr.models import StarboardMessage, StarrGuild


stars = tanjun.Component(name="stars").add_check(tanjun.checks.GuildCheck())


async def get_reaction_event_info(
    event: hikari.GuildReactionAddEvent |
        hikari.GuildReactionDeleteEmojiEvent |
        hikari.GuildReactionDeleteEvent,
    bot: StarrBot,
) -> tuple[hikari.Message, StarrGuild, int] | None:
    if event.emoji_name != bot.star:
        # Ignore non star emojis
        return

    if not (guild := bot.guilds.get(event.guild_id)):
        # Grab the guild from cache, or construct it from the db
        # if not cached.
        guild = await StarrGuild.from_db(bot.db, event.guild_id)

    if not guild.configured:
        # The guild hasnt configured their starboard yet.
        return

    try:
        message = await bot.rest.fetch_message(event.channel_id, event.message_id)
        # We could ignore reactions from the messages author, but this
        # is inconsistent because during discord outages, or bot
        # downtime we can never be sure again who it was that reacted.
        # On top of this, when the next person reacts, the authors
        # reaction will get counted.
    except hikari.NotFoundError:
        # The message got deleted.
        return

    # The total number of star emojis.
    count = sum(map(lambda r: r.emoji == bot.star, message.reactions))

    return message, guild, count


async def handle_star_add_event(
    bot: StarrBot,
    message: hikari.Message,
    guild: StarrGuild,
    count: int,
) -> None:
    if count >= guild.threshold:
        # This message is a star!
        starboard_message = await StarboardMessage.from_reference(bot.db, message.id, guild)

        if not starboard_message:
            # This is a brand new starboard entry.
            await StarboardMessage.create_new(bot.rest, bot.db, message, count, guild)

        else:
            # This is an existing starboard entry.
            await starboard_message.update(bot.rest, bot.db, message, count, guild)


async def handle_star_delete_event(
    bot: StarrBot,
    message: hikari.Message,
    guild: StarrGuild,
    count: int,
) -> None:
    if count < guild.threshold:
        # This message is no longer a star.
        starboard_message = await StarboardMessage.from_reference(bot.db, message.id, guild)

        if not starboard_message:
            # This message is not in the database, and thus we can ignore it.
            return

        # Delete the starboard entry, and remove from the db.
        await starboard_message.delete(bot.rest, bot.db)


@stars.with_listener(hikari.GuildReactionAddEvent)
async def on_reaction_add(
    event: hikari.GuildReactionAddEvent,
    bot: StarrBot = tanjun.inject(type=StarrBot)
) -> None:
    if not (event_data := await get_reaction_event_info(event, bot)):
        # If this returns None we don't care about the event.
        return

    message, guild, count = event_data
    await handle_star_add_event(bot, message, guild, count)


@stars.with_listener(hikari.GuildReactionDeleteEvent)
async def on_reaction_delete(
    event: hikari.GuildReactionDeleteEvent,
    bot: StarrBot = tanjun.inject(type=StarrBot)
) -> None:
    if not (event_data := await get_reaction_event_info(event, bot)):
        # If this returns None we don't care about the event.
        return

    message, guild, count = event_data
    await handle_star_delete_event(bot, message, guild, count)


@stars.with_listener(hikari.GuildReactionDeleteEmojiEvent)
async def on_reaction_emoji_delete(
    event: hikari.GuildReactionDeleteEmojiEvent,
    bot: StarrBot = tanjun.inject(type=StarrBot)
) -> None:
    if not (event_data := await get_reaction_event_info(event, bot)):
        # If this returns None we don't care about the event.
        return

    message, guild, count = event_data
    await handle_star_delete_event(bot, message, guild, count)


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(stars.copy())
