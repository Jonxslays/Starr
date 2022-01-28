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

import datetime
import math
import secrets

import hikari
import tanjun

from starr.db import Database


class Paginator:

    __slots__ = (
        "ctx",
        "bot",
        "title",
        "description",
        "fields",
        "per_page",
        "page",
        "embed",
        "converted",
        "id_hash",
        "message",
        "components",
        "num_pages",
    )

    def __init__(
        self,
        ctx: tanjun.abc.Context,
        bot: hikari.GatewayBot,
        *,
        title: str,
        description: str,
        fields: list[tuple[str, ...]],
        per_page: int = 5,
    ) -> None:
        self.ctx = ctx
        self.bot = bot
        self.title = title
        self.description = description
        self.fields = fields
        self.per_page = per_page
        self.page = 0
        self.converted: list[hikari.Embed] = []
        self.num_pages = math.ceil(len(self.fields) / self.per_page)
        self.id_hash = secrets.token_urlsafe(8)
        self.message: hikari.Message | None = None
        self.components = self.generate_buttons()
        self.embed = hikari.Embed(
            title=title,
            description=description,
            color=hikari.Color(0x19FA3B),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

    def get_new_embed(self) -> hikari.Embed:
        return hikari.Embed(
            title=self.title,
            description=self.description,
            color=hikari.Color(0x19FA3B),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        ).set_thumbnail(self.ctx.author.avatar_url or self.ctx.author.default_avatar_url)

    async def paginate(self, timeout: int | float) -> None:
        e = self.get_new_embed()
        current = 0

        for field in self.fields:
            e.add_field(*field)

            if current == self.per_page - 1:
                self.converted.append(e)
                e = self.get_new_embed()
                current = 0
                continue

            current += 1

        self.converted.append(e)
        self.message = await self.ctx.respond(
            self.converted[self.page], components=self.components, ensure_result=True
        )
        await self.listen(timeout)

    def generate_buttons(self) -> list[hikari.api.ActionRowBuilder]:
        buttons = {
            "first": "\u23EE\uFE0F",
            "prev": "\u23EA",
            "stop": "\u23F9\uFE0F",
            "next": "\u23E9",
            "last": "\u23ED\uFE0F",
        }

        row = self.ctx.rest.build_action_row()

        for key, button in buttons.items():
            style = hikari.ButtonStyle.PRIMARY if key != "stop" else hikari.ButtonStyle.DANGER
            (row.add_button(style, f"{self.id_hash}-{key}").set_emoji(button).add_to_container())  # type: ignore

        return [row]

    async def respond(
        self,
        interaction: hikari.ComponentInteraction | None,
        components: list[hikari.api.ActionRowBuilder],
    ) -> None:
        assert self.message is not None

        if not interaction:
            await self.message.edit(self.converted[self.page], components=components)
            return None

        try:
            await interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_UPDATE,
                self.converted[self.page],
                components=components,
            )

        except hikari.NotFoundError:
            await self.message.edit(self.converted[self.page], components=components)

    async def listen(self, timeout: int | float) -> None:
        with self.bot.stream(hikari.InteractionCreateEvent, timeout=timeout).filter(
            lambda e: (
                isinstance(e.interaction, hikari.ComponentInteraction)
                and e.interaction.user == self.ctx.author
                and e.interaction.message == self.message
            )
        ) as stream:
            async for event in stream:
                assert isinstance(event.interaction, hikari.ComponentInteraction)
                cid = event.interaction.custom_id

                if cid == f"{self.id_hash}-stop":
                    break

                elif cid == f"{self.id_hash}-next":
                    if self.page < self.num_pages - 1:
                        self.page += 1

                elif cid == f"{self.id_hash}-prev":
                    if self.page != 0:
                        self.page -= 1

                elif cid == f"{self.id_hash}-first":
                    self.page = 0

                elif cid == f"{self.id_hash}-last":
                    self.page = self.num_pages - 1

                await self.respond(event.interaction, self.components)

        await self.respond(None, [])


class StarrGuild:

    __slots__ = ("_guild_id", "_prefix", "_star_channel", "_threshold")

    def __init__(
        self,
        guild_id: int,
        prefix: str,
        star_channel: int = 0,
        threshold: int = 5,
    ) -> None:
        self._guild_id = guild_id
        self._prefix = prefix
        self._star_channel = star_channel
        self._threshold = threshold

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
            "INSERT INTO starboard_messages (StarMessageID, ReferenceID) VALUES ($1, $2) ON CONFLICT DO NOTHING;",
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
        origial_message: hikari.Message,
        count: int,
        guild: StarrGuild,
    ) -> hikari.Message:
        embed = (
            hikari.Embed(
                title=f"Jump to message",
                url=origial_message.make_link(guild.guild_id),
                color=hikari.Color.from_hex_code("#fcd303"),
                description=origial_message.content,
                timestamp=origial_message.timestamp,
            )
            .set_author(
                name=f"{origial_message.author.username}#{origial_message.author.discriminator}",
                icon=origial_message.author.avatar_url
                or origial_message.author.default_avatar_url,
            )
            .set_footer(text=f"ID: {origial_message.id}")
        )

        if origial_message.attachments:
            embed.set_image(origial_message.attachments[0])

        new_message = await rest.create_message(
            content=f"You're a \u2B50 x{count}!\n",
            channel=guild.star_channel,
            embed=embed,
        )

        starboard_message = cls(new_message.id, origial_message.id, guild)
        await starboard_message.db_insert(db)
        return new_message
