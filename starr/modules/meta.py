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
import time

import hikari
import lightbulb

from starr import utils
from starr.bot import StarrBot

meta = utils.Plugin("meta", "Statistical commands.")


@meta.command
@lightbulb.set_help(docstring=True)
@lightbulb.command("ping", "Starr's latency.")
@lightbulb.implements(lightbulb.PrefixCommand)
async def ping_command(ctx: utils.PrefixContext) -> None:
    """Why is Starr so slow?"""
    start = time.perf_counter()
    await ctx.respond("wait what...")
    elapsed = time.perf_counter() - start

    await ctx.edit_last_response(
        f"Gateway: {ctx.bot.heartbeat_latency * 1000:,.0f} ms\nRest: {elapsed * 1000:,.0f} ms"
    )


@meta.command
@lightbulb.set_help(docstring=True)
@lightbulb.option("user", "The user to get info on.", type=hikari.Member)
@lightbulb.command("userinfo", "Get information about a user.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def user_info_cmd(ctx: utils.Context) -> None:
    """For when you feel like being a stalker."""
    user: hikari.Member = ctx.options.user

    color = None
    if roles := user.get_roles():
        roles = sorted(roles, key=lambda r: r.position, reverse=True)

        for role in roles:
            if role.color:
                color = role.color
                break

    if not color:
        color = hikari.Color(0x31A6E0)

    e = (
        hikari.Embed(
            title=f"User info for {user}",
            description=f"ID: {user.id}",
            color=color,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        .set_thumbnail(user.avatar_url or user.default_avatar_url)
        .set_image(user.banner_url)
        .add_field(
            "Created on",
            f"<t:{user.created_at.time():.0f}:f> (<t:{user.created_at.time():.0f}:R>)",
        )
        .add_field(
            "Joined on",
            f"<t:{user.joined_at.time():.0f}:f> (<t:{user.joined_at.time():.0f}:R>)",
        )
        .add_field(
            "Roles",
            ", ".join(
                (r.mention if ctx.guild_id != r.id else "@everyone" for r in roles) or "No roles?"
            ),
        )
    )

    await ctx.respond(e)


def load(bot: StarrBot) -> None:
    bot.add_plugin(meta)
