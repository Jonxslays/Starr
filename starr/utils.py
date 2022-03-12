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

import abc
import datetime
import logging
import math
import secrets
import typing as t
from logging.handlers import RotatingFileHandler

import hikari
import lightbulb

from starr.bot import StarrBot


def configure_logging() -> None:
    log = logging.getLogger("root")
    log.setLevel(logging.INFO)

    rfh = RotatingFileHandler(
        "./starr/data/logs/main.log",
        maxBytes=521288,  # 512KB
        encoding="utf-8",
        backupCount=10,
    )

    ff = logging.Formatter(
        f"[%(asctime)s] %(levelname)s ||| %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    rfh.setFormatter(ff)
    log.addHandler(rfh)


class Plugin(lightbulb.Plugin):
    @property
    def bot(self) -> StarrBot:
        return t.cast(StarrBot, self.app)


class Context(lightbulb.Context):
    @property
    def bot(self) -> StarrBot:
        return t.cast(StarrBot, self.app)

    @property
    @abc.abstractmethod
    def guild_id(self) -> hikari.Snowflakeish:
        ...


class SlashContext(Context, lightbulb.SlashContext):
    ...


class PrefixContext(Context, lightbulb.PrefixContext):
    ...


class MessageContext(Context, lightbulb.MessageContext):
    ...


class UserContext(Context, lightbulb.UserContext):
    ...


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
        "inline",
    )

    def __init__(
        self,
        ctx: Context,
        *,
        title: str,
        description: str,
        fields: list[tuple[str, ...]],
        per_page: int = 5,
        inline: bool = False,
    ) -> None:
        self.ctx = ctx
        self.bot = ctx.bot
        self.title = title
        self.description = description
        self.fields = fields
        self.inline = inline
        self.per_page = per_page
        self.page = 0
        self.converted: list[list[tuple[str, ...]]] = []
        self.num_pages = math.ceil(len(self.fields) / self.per_page)
        self.id_hash = secrets.token_urlsafe(8)
        self.message: hikari.Message | None = None
        self.embed = hikari.Embed(
            title=title,
            description=description,
            color=hikari.Color(0x19FA3B),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

    def get_next_embed(self, fields: list[tuple[str, ...]]) -> hikari.Embed:
        embed = hikari.Embed(
            title=self.title,
            description=self.description,
            color=hikari.Color(0x19FA3B),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        ).set_thumbnail(self.ctx.author.avatar_url or self.ctx.author.default_avatar_url)

        for field in fields:
            embed.add_field(field[0], field[1], inline=self.inline)

        return embed

    async def paginate(self, timeout: int | float) -> None:
        current = 0
        this_list: list[tuple[str, ...]] = []

        for field in self.fields:
            this_list.append(field)

            if current == self.per_page - 1:
                self.converted.append(this_list)
                this_list = []
                current = 0
                continue

            current += 1

        self.converted.append(this_list)
        response = await self.ctx.respond(
            self.get_next_embed(self.converted[self.page]),
            components=self.generate_buttons(self.page),
        )
        self.message = await response.message()
        await self.listen(timeout)

    def generate_buttons(self, page: int) -> list[hikari.api.ActionRowBuilder]:
        buttons = {
            "first": "\u23EE\uFE0F",
            "prev": "\u23EA",
            "stop": "\u2716\uFE0F",
            "next": "\u23E9",
            "last": "\u23ED\uFE0F",
        }

        row = self.ctx.bot.rest.build_action_row()

        for key, button in buttons.items():
            style = hikari.ButtonStyle.PRIMARY if key != "stop" else hikari.ButtonStyle.DANGER
            if (
                page == 0
                and key in ("first", "prev")
                or page >= self.num_pages - 1
                and key in ("last", "next")
            ):
                (
                    row.add_button(style, f"{self.id_hash}-{key}")
                    .set_emoji(button)
                    .set_is_disabled(True)
                    .add_to_container()
                )
            else:
                (
                    row.add_button(style, f"{self.id_hash}-{key}")
                    .set_emoji(button)
                    .set_is_disabled(False)
                    .add_to_container()
                )

        return [row]

    async def respond(
        self,
        interaction: hikari.ComponentInteraction | None,
        components: list[hikari.api.ActionRowBuilder],
    ) -> None:
        assert self.message is not None
        embed = self.get_next_embed(self.converted[self.page])

        if not interaction:
            await self.message.edit(embed, components=components)
            return None

        try:
            await interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_UPDATE,
                embed,
                components=components,
            )

        except hikari.NotFoundError:
            await self.message.edit(embed, components=components)

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

                await self.respond(event.interaction, self.generate_buttons(self.page))

        await self.respond(None, [])
