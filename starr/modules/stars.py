# Copyright (c) 2021-present, Jonxslays
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import hikari

from starr import utils
from starr.bot import StarrBot
from starr.models import StarboardMessage
from starr.models import StarrGuild

stars = utils.Plugin("stars", "Starboard related plugin.", include_datastore=True)
stars.d.star = "\u2B50"


async def get_reaction_event_info(
    event: hikari.GuildReactionAddEvent | hikari.GuildReactionDeleteEvent,
    bot: StarrBot,
) -> tuple[hikari.Message, StarrGuild, int] | None:
    if event.emoji_name != stars.d.star:
        # Ignore non star emojis
        return None

    if not (guild := bot.guilds.get(event.guild_id)):
        # Grab the guild from cache, or construct it from the db
        # if not cached.
        guild = await StarrGuild.from_db(bot.db, event.guild_id)

    if not guild.star_channel or event.channel_id in guild.star_blacklist:
        # The guild hasn't configured their starboard yet
        # or this channel is in their starboard blacklist.
        return None

    try:
        message = await bot.rest.fetch_message(event.channel_id, event.message_id)
        # We could ignore reactions from the messages author, but this
        # is inconsistent because during discord outages, or bot
        # downtime we can never be sure again who it was that reacted.
        # On top of this, when the next person reacts, the authors
        # reaction will get counted.
    except hikari.NotFoundError:
        # The message got deleted.
        return None

    # The total number of star emojis.
    count = sum(map(lambda r: r.count if r.emoji == stars.d.star else 0, message.reactions))

    return message, guild, count


@stars.listener(hikari.GuildReactionAddEvent)
async def on_reaction_add(
    event: hikari.GuildReactionAddEvent,
) -> None:
    if not (event_data := await get_reaction_event_info(event, stars.bot)):
        # If this returns None we don't care about the event.
        return None

    message, guild, count = event_data
    if message.channel_id == guild.star_channel:
        return None

    if count >= guild.threshold:
        # This message is a star!
        starboard_message = await StarboardMessage.from_reference(stars.bot.db, message.id, guild)

        if not starboard_message:
            # This is a brand new starboard entry.
            await StarboardMessage.create_new(stars.bot.rest, stars.bot.db, message, count, guild)

        else:
            # This is an existing starboard entry.
            await starboard_message.update(stars.bot.rest, stars.bot.db, message, count, guild)


@stars.listener(hikari.GuildReactionDeleteEvent)
async def on_reaction_delete(event: hikari.GuildReactionDeleteEvent) -> None:
    if not (event_data := await get_reaction_event_info(event, stars.bot)):
        # If this returns None we don't care about the event.
        return None

    message, guild, count = event_data
    starboard_message = await StarboardMessage.from_reference(stars.bot.db, message.id, guild)

    if not starboard_message:
        # This message is not in the database and thus we can ignore it.
        return None

    if count < guild.threshold:
        # This message is no longer a star.
        await starboard_message.delete(stars.bot.rest, stars.bot.db)

    else:
        # This is an existing starboard entry, and still a star!
        await starboard_message.update(stars.bot.rest, stars.bot.db, message, count, guild)


@stars.listener(hikari.GuildMessageDeleteEvent)
@stars.listener(hikari.GuildReactionDeleteEmojiEvent)
@stars.listener(hikari.GuildReactionDeleteAllEvent)
async def handle_guaranteed_delete(
    event: hikari.GuildMessageDeleteEvent
    | hikari.GuildReactionDeleteEmojiEvent
    | hikari.GuildReactionDeleteAllEvent,
) -> None:
    if not (guild := stars.bot.guilds.get(event.guild_id)):
        # Grab the guild from cache, or construct it from the db
        # if not cached.
        guild = await StarrGuild.from_db(stars.bot.db, event.guild_id)

    if not guild.star_channel:
        # The guild hasn't configured their starboard yet.
        return None

    message = await StarboardMessage.from_reference(stars.bot.db, event.message_id, guild)

    # Delete message from db and starboard, it has no more reactions.
    return await message.delete(stars.bot.rest, stars.bot.db) if message else None


def load(bot: StarrBot) -> None:
    bot.add_plugin(stars)
