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

import hikari
import tanjun

from starr.bot import StarrBot


admin = (
    tanjun.Component(name="admin")
    .add_check(tanjun.checks.GuildCheck())
    .add_check(tanjun.checks.AuthorPermissionCheck(hikari.Permissions.ADMINISTRATOR))
)

config = admin.with_slash_command(
    tanjun.slash_command_group("config", "Starr configuration options.")
)


@config.with_command
@tanjun.with_int_slash_option(
    "threshold", "Sets the number of stars a message must receive.", default=0, min_value=1
)
@tanjun.with_channel_slash_option(
    "channel", "Sets the starboard channel.", types=(hikari.GuildTextChannel,), default=None
)
@tanjun.as_slash_command("starboard", "Configures Starr for this guild.")
async def configure_starboard_cmd(
    ctx: tanjun.abc.SlashContext,
    threshold: int,
    channel: hikari.InteractionChannel | None,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    assert ctx.guild_id is not None

    updates: list[tuple[t.Any, ...]] = []
    responses: list[str] = []

    if channel:
        guild = bot.guilds[ctx.guild_id]
        guild.configured = 1
        guild.star_channel = channel.id

        updates.append(
            (
                "UPDATE guilds SET StarChannel = $1, Configured = 1 WHERE GuildID = $2;",
                channel.id,
                ctx.guild_id,
            )
        )
        responses.append(f"Successfully updated starboard channel to <#{channel.id}>.")

    if threshold:
        updates.append(
            (
                "UPDATE guilds SET Threshold = $1 WHERE GuildID = $2;",
                threshold,
                ctx.guild_id,
            )
        )
        responses.append(f"Successfully updated starboard star threshold to {threshold}.")

    for update in updates:
        await bot.db.execute(*update)

    if responses:
        await ctx.respond("\n".join(responses))
    else:
        await ctx.respond("Nothing happened...")


@config.with_command
@tanjun.with_str_slash_option("value", "The new prefix to set.")
@tanjun.as_slash_command("prefix", "Configures message command prefix for this guild.")
async def configure_prefix_cmd(
    ctx: tanjun.abc.SlashContext,
    value: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    assert ctx.guild_id is not None
    await bot.db.fetch_row("UPDATE guilds SET Prefix = $1 WHERE GuildID = $2;", value, ctx.guild_id)

    guild = bot.guilds[ctx.guild_id]
    guild.prefix = value

    await ctx.respond(f"Successfully updated message command prefix to `{value}`")


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(admin.copy())
