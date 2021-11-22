import hikari
import tanjun

from starr.bot import StarrBot
from starr.models import StarboardMessage, StarrGuild


stars = tanjun.Component(name="stars").add_check(tanjun.checks.GuildCheck())


@stars.with_listener(hikari.GuildReactionAddEvent)
async def on_reaction_add(
    event: hikari.GuildReactionAddEvent,
    bot: StarrBot = tanjun.inject(type=StarrBot)
) -> None:
    if event.emoji_name != bot.star:
        return

    message = await bot.rest.fetch_message(event.channel_id, event.message_id)
    if message.author.is_bot: # or message.author.id == event.user_id:
        return

    if not (guild := bot.guilds.get(event.guild_id)):
        guild = await StarrGuild.from_db(bot.db, event.guild_id)

    if not guild.configured:
        print("Skipping due to no configuration")
        return

    num_stars = len([filter(lambda r: r.emoji == bot.star, message.reactions)])

    if num_stars >= guild.threshold:
        starboard_message = await StarboardMessage.from_reference(bot.db, message.id, guild)

        if not starboard_message:
            # This is a brand new starboard entry.
            await StarboardMessage.create_new(bot.rest, bot.db, message, num_stars, guild)

            # TODO: Continue

@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(stars.copy())
