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
import tanjun
from tanjun.conversion import from_datetime

from starr import utils
from starr.bot import StarrBot

meta = tanjun.Component(name="meta")


@meta.with_command
@utils.with_help("Returns Starr's latency.", usage="ping")
@tanjun.as_message_command("ping")
async def ping_message_cmd(
    ctx: tanjun.abc.Context, bot: StarrBot = tanjun.inject(type=StarrBot)
) -> None:
    start = time.perf_counter()
    message = await ctx.respond(".", ensure_result=True)
    elapsed = time.perf_counter() - start

    await message.edit(
        f"**Gateway**: {bot.heartbeat_latency * 1000:,.0f} ms\n**REST**: {elapsed * 1000:,.0f} ms"
    )


@meta.with_command
@tanjun.with_member_slash_option("user", "The user to get info on.")
@tanjun.as_slash_command("userinfo", "Get information about a user.")
@utils.prepare_slash
@meta.with_command
@tanjun.with_argument("user", converters=int)
@tanjun.with_parser
@utils.with_help(
    "Get information about a user.",
    args=("user (int): The user to get info on.",),
    usage="userinfo 1234567898769420",
)
@tanjun.as_message_command("userinfo")
async def user_info_cmd(
    ctx: tanjun.abc.SlashContext,
    user: hikari.Member | int,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    assert ctx.guild_id is not None

    if isinstance(user, int):
        user = await bot.rest.fetch_member(ctx.guild_id, user)

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
            f"{from_datetime(user.created_at)} ({from_datetime(user.created_at, style='R')})",
        )
        .add_field(
            "Joined on",
            f"{from_datetime(user.joined_at)} ({from_datetime(user.joined_at, style='R')})",
        )
        .add_field(
            "Roles",
            ", ".join(
                (r.mention if ctx.guild_id != r.id else "@everyone" for r in roles) or "No roles?"
            ),
        )
    )

    await ctx.respond(e)


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(meta.copy())
