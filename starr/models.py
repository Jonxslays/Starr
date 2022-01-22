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

    __slots__ = ("_guild_id", "_prefix", "_star_channel", "_configured", "_threshold")

    def __init__(
        self,
        guild_id: int,
        prefix: str,
        star_channel: int = 0,
        configured: int = 0,
        threshold: int = 1,
    ) -> None:
        self._guild_id = guild_id
        self._prefix = prefix
        self._star_channel = star_channel
        self._configured = configured
        self._threshold = threshold

    @property
    def guild_id(self) -> int:
        return self._guild_id

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def star_channel(self) -> int:
        return self._star_channel

    @property
    def configured(self) -> int:
        return self._configured

    @property
    def threshold(self) -> int:
        return self._threshold

    @classmethod
    async def from_db(cls, db: Database, guild_id: int) -> StarrGuild:
        data = await db.row("SELECT * FROM guilds WHERE GuildID = $1;", guild_id)
        return cls(*data)

    @classmethod
    async def default_with_insert(cls, db: Database, guild_id: int) -> StarrGuild:
        data = await db.row(
            "INSERT INTO guilds (GuildID) VALUES ($1) ON CONFLICT DO NOTHING RETURNING *;",
            guild_id,
        )

        if not data:
            return await cls.from_db(db, guild_id)

        return cls(*data)


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
            "DELETE FROM starboard_messages WHERE ReferenceID = $1", self.reference_id
        )
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
        message: hikari.Message,
        count: int,
        guild: StarrGuild,
    ) -> None:
        try:
            message = await rest.fetch_message(guild.star_channel, self._message_id)

        except hikari.NotFoundError:
            message = await self.create_new(rest, db, message, count, guild)
            self._message_id = message.id
            await self.db_update(db)

        else:
            await message.edit(content=f"You're a \u2B50 x{count}!\n")

    @classmethod
    async def from_reference(
        cls,
        db: Database,
        reference_id: int,
        guild: StarrGuild,
    ) -> StarboardMessage | None:
        data = await db.fetch(
            "SELECT StarMessageID FROM starboard_messages " "WHERE ReferenceID = $1",
            reference_id,
        )

        if data:
            return cls(data, reference_id, guild)

        return None

    @classmethod
    async def create_new(
        cls,
        rest: hikari.api.RESTClient,
        db: Database,
        message: hikari.Message,
        count: int,
        guild: StarrGuild,
    ) -> hikari.Message:
        embed = (
            hikari.Embed(
                title=f"Jump to message",
                url=message.make_link(guild.guild_id),
                color=hikari.Color.from_hex_code("#fcd303"),
                description=message.content,
                timestamp=message.timestamp,
            )
            .set_author(
                name=f"{message.author.username}#{message.author.discriminator}",
                icon=message.author.avatar_url or message.author.default_avatar_url,
            )
            .set_footer(text=f"ID: {message.id}")
        )

        if message.attachments:
            embed.set_image(message.attachments[0])

        new_message = await rest.create_message(
            content=f"You're a \u2B50 x{count}!\n",
            channel=guild.star_channel,
            embed=embed,
        )

        starboard_message = cls(new_message.id, message.id, guild)
        await starboard_message.db_insert(db)
        return new_message
