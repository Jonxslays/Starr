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

from starr.db import Database


class StarrGuild:
    __slots__ = ("_guild_id", "_prefix", "_star_channel", "_threshold", "_star_blacklist")

    def __init__(
        self,
        guild_id: int,
        prefix: str,
        star_channel: int = 0,
        threshold: int = 5,
        star_blacklist: list[int] = [],
    ) -> None:
        self._guild_id = guild_id
        self._prefix = prefix
        self._star_channel = star_channel
        self._threshold = threshold
        self._star_blacklist = star_blacklist

    @property
    def guild_id(self) -> int:
        return self._guild_id

    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, value: str) -> None:
        self._prefix = value

    @property
    def star_channel(self) -> int:
        return self._star_channel

    @star_channel.setter
    def star_channel(self, value: int) -> None:
        self._star_channel = value

    @property
    def star_blacklist(self) -> list[int]:
        return self._star_blacklist

    @property
    def threshold(self) -> int:
        return self._threshold

    @threshold.setter
    def threshold(self, value: int) -> None:
        self._threshold = value

    @classmethod
    async def from_db(cls, db: Database, guild_id: int) -> StarrGuild:
        data = await db.fetch_row("SELECT * FROM guilds WHERE GuildID = $1;", guild_id)
        return cls(*data)

    @classmethod
    async def default_with_insert(cls, db: Database, guild_id: int) -> StarrGuild:
        data = await db.fetch_row(
            "INSERT INTO guilds (GuildID) VALUES ($1) ON CONFLICT DO NOTHING RETURNING *;",
            guild_id,
        )

        if not data:
            return await cls.from_db(db, guild_id)

        return cls(*data)

    async def add_channel_to_blacklist(self, db: Database, channel_id: int) -> None:
        self._star_blacklist.append(channel_id)
        await db.execute(
            "UPDATE guilds "
            "SET StarBlacklist = array_append(StarBlacklist, $1) "
            "WHERE GuildID = $2;",
            channel_id,
            self._guild_id,
        )

    async def remove_channel_from_blacklist(self, db: Database, channel_id: int) -> None:
        try:
            self._star_blacklist.remove(channel_id)
        except ValueError:
            pass
        else:
            await db.execute(
                "UPDATE guilds SET StarBlacklist = $1 WHERE GuildID = $2;",
                self._star_blacklist,
                self._guild_id,
            )


class StarboardMessage:
    __slots__ = ("_message_id", "_reference_id", "_guild")

    def __init__(self, message_id: int, reference_id: int, guild: StarrGuild) -> None:
        self._message_id = message_id
        self._reference_id = reference_id
        self._guild = guild

    @property
    def message_id(self) -> int:
        return self._message_id

    @property
    def reference_id(self) -> int:
        return self._reference_id

    @property
    def guild(self) -> StarrGuild:
        return self._guild

    async def db_insert(self, db: Database) -> None:
        await db.execute(
            "INSERT INTO starboard_messages (StarMessageID, ReferenceID) "
            "VALUES ($1, $2) ON CONFLICT DO NOTHING;",
            self._message_id,
            self._reference_id,
        )

    async def db_update(self, db: Database) -> None:
        await db.execute(
            "UPDATE starboard_messages SET StarMessageID = $1 WHERE ReferenceID = $2;",
            self._message_id,
            self._reference_id,
        )

    async def delete(
        self,
        rest: hikari.api.RESTClient,
        db: Database,
    ) -> None:
        try:
            await rest.delete_message(self._guild.star_channel, self._message_id)

        except hikari.NotFoundError:
            # The starboard message was already deleted.
            pass

        await db.execute(
            "DELETE FROM starboard_messages WHERE StarMessageID = $1;", self._message_id
        )

    async def update(
        self,
        rest: hikari.api.RESTClient,
        db: Database,
        original_message: hikari.Message,
        count: int,
        guild: StarrGuild,
    ) -> None:
        try:
            await rest.edit_message(
                guild.star_channel, self._message_id, f"You're a \u2B50 x{count}!\n"
            )

        except hikari.NotFoundError:
            message = await self.create_new(rest, db, original_message, count, guild)
            self._message_id = message.id
            await self.db_update(db)

    @classmethod
    async def from_reference(
        cls,
        db: Database,
        reference_id: int,
        guild: StarrGuild,
    ) -> StarboardMessage | None:
        data = await db.fetch_one(
            "SELECT StarMessageID FROM starboard_messages WHERE ReferenceID = $1", reference_id
        )

        if data:
            return cls(data, reference_id, guild)

        return None

    @classmethod
    async def create_new(
        cls,
        rest: hikari.api.RESTClient,
        db: Database,
        original_message: hikari.Message,
        count: int,
        guild: StarrGuild,
    ) -> hikari.Message:
        reference_channel = await rest.fetch_channel(original_message.channel_id)

        embed = (
            hikari.Embed(
                title=f"Jump to message in #{reference_channel.name}",
                url=original_message.make_link(guild.guild_id),
                color=hikari.Color.from_hex_code("#fcd303"),
                description=original_message.content,
                timestamp=original_message.timestamp,
            )
            .set_author(
                name=f"{original_message.author.username}#{original_message.author.discriminator}",
                icon=original_message.author.avatar_url
                or original_message.author.default_avatar_url,
            )
            .set_footer(text=f"ID: {original_message.id}")
        )

        if original_message.attachments:
            embed.set_image(original_message.attachments[0])

        new_message = await rest.create_message(
            content=f"You're a \u2B50 x{count}!\n",
            channel=guild.star_channel,
            embeds=(embed, *(e for e in original_message.embeds[0:9] if e.description)),
        )

        starboard_message = cls(new_message.id, original_message.id, guild)
        await starboard_message.db_insert(db)
        return new_message
