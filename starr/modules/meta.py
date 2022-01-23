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

from starr.bot import StarrBot

meta = tanjun.Component(name="meta").add_check(tanjun.checks.GuildCheck())


@meta.with_command
@tanjun.as_slash_command("ping", "Returns Starr's latency.")
async def ping(ctx: tanjun.abc.Context, bot: StarrBot = tanjun.inject(type=StarrBot)) -> None:
    start = time.perf_counter()
    message = await ctx.respond(".", ensure_result=True)
    elapsed = time.perf_counter() - start

    await message.edit(
        f"Gateway: {bot.heartbeat_latency * 1000:,.2f} ms\nRest: {elapsed * 1000:,.2f} ms"
    )


@meta.with_command
@tanjun.with_member_slash_option("member", "The member to get information on.")
@tanjun.as_slash_command("userinfo", "Get information about a member.", always_defer=True)
async def user_info_slash_cmd(
    ctx: tanjun.abc.SlashContext,
    member: hikari.Member,
) -> None:
    if role := member.get_top_role():
        color = role.color
    else:
        color = hikari.Color(0x31a6e0)

    e = (
        hikari.Embed(
            title=f"User info for {member}",
            description=f"ID: {member.id}",
            color=color,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        .set_thumbnail(member.avatar_url or member.default_avatar_url)
        .set_image(member.banner_url)
        .add_field(
            "Created on",
            from_datetime(member.created_at) +
            f" ({from_datetime(member.created_at, style='R')})",
        )
        .add_field(
            "Joined on",
            from_datetime(member.joined_at) +
            f" ({from_datetime(member.joined_at, style='R')})",
        )
        .add_field(
            "Roles",
            ", ".join(
                r.mention for r in (member.get_roles() or await member.fetch_roles())
                if "everyone" not in r.name
            )
        )
    )

    if presence := member.get_presence():
        if presence.activities:
            activity = presence.activities[0]
            activity_type = hikari.ActivityType(activity.type).name.title()

            e.add_field(
                "Activity",
                f"{'' if 'custom' in activity_type else activity_type + ' '}{activity.name}",
                inline=True,
            )

        e.add_field("Status", presence.visible_status, inline=True)

    await ctx.respond(e)


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(meta.copy())
