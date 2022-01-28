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

import typing as t
from os import environ
from pathlib import Path

import hikari
import tanjun

from starr.db import Database
from starr.models import StarrGuild

SubscriptionsT = dict[t.Type[hikari.Event], t.Callable[..., t.Coroutine[t.Any, t.Any, None]]]


class StarrBot(hikari.GatewayBot):

    __slots__ = ("star", "db", "guilds", "log", "client", "my_id")

    def __init__(self) -> None:
        super().__init__(
            token=environ["TOKEN"],
            intents=hikari.Intents.GUILDS
            | hikari.Intents.GUILD_MESSAGE_REACTIONS
            | hikari.Intents.GUILD_MESSAGES,
        )

        default_guilds = (
            (environ["DEV"], environ["PROD"]) if int(environ["IS_PROD"]) else (environ["DEV"],)
        )

        self.star = "\u2B50"
        self.db = Database()
        self.guilds: dict[int, StarrGuild] = {}
        self.client = (
            tanjun.Client.from_gateway_bot(
                self,
                mention_prefix=True,
                declare_global_commands=tuple(map(int, default_guilds)),
            )
            # .set_hooks(ErrorHooks) # FIXME: stops error parsing?
            .add_check(tanjun.checks.GuildCheck())
            .set_prefix_getter(self.resolve_prefix)
            .load_modules(*Path("./starr/modules").glob("[!_]*.py"))
            .set_auto_defer_after(2)
        )

        self.subscribe(hikari.StartingEvent, self.on_starting)
        self.subscribe(hikari.StartedEvent, self.on_started)
        self.subscribe(hikari.StoppedEvent, self.on_stopped)
        self.subscribe(hikari.GuildAvailableEvent, self.on_guild_available)
        self.subscribe(hikari.GuildJoinEvent, self.on_guild_available)

    async def getch_member(self, guild_id: int, member_id: int) -> hikari.Member:
        return self.cache.get_member(guild_id, member_id) or await self.rest.fetch_member(
            guild_id, member_id
        )

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        await self.db.connect()

    async def on_started(self, _: hikari.StartedEvent) -> None:
        if data := await self.db.fetch_rows("SELECT * FROM guilds;"):
            for guild in data:
                obj = StarrGuild(*guild)
                self.guilds[obj.guild_id] = obj

        self.my_id = me.id if (me := self.get_me()) else (await self.rest.fetch_my_user()).id

    async def on_stopped(self, _: hikari.StoppingEvent) -> None:
        await self.db.close()

    async def on_guild_available(
        self, event: hikari.GuildAvailableEvent | hikari.GuildJoinEvent
    ) -> None:
        if event.guild_id not in self.guilds:
            guild = await StarrGuild.default_with_insert(self.db, event.guild_id)
            self.guilds[guild.guild_id] = guild

    async def resolve_prefix(self, ctx: tanjun.context.MessageContext) -> tuple[str, ...]:
        if ctx.guild_id and (guild := self.guilds.get(ctx.guild_id)):
            return (guild.prefix,)

        return ("./",)
