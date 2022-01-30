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

import hikari
import tanjun

from starr import models
from starr.bot import StarrBot

admin = tanjun.Component(name="admin").add_check(
    tanjun.checks.AuthorPermissionCheck(
        hikari.Permissions.ADMINISTRATOR,
        error_message="You're not allowed to do that.",
    )
)

########################################################################
# START CONFIG
########################################################################

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

    responses: list[str] = []
    guild = bot.guilds[ctx.guild_id]

    if channel:
        guild.star_channel = channel.id

        await bot.db.execute(
            "UPDATE guilds SET StarChannel = $1 WHERE GuildID = $2;",
            channel.id,
            ctx.guild_id,
        )
        responses.append(f"Successfully updated starboard channel to <#{channel.id}>.")

    if threshold:
        guild.threshold = threshold

        await bot.db.execute(
            "UPDATE guilds SET Threshold = $1 WHERE GuildID = $2;",
            threshold,
            ctx.guild_id,
        )
        responses.append(f"Successfully updated starboard star threshold to {threshold}.")

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
    await bot.db.fetch_row(
        "UPDATE guilds SET Prefix = $1 WHERE GuildID = $2;", value, ctx.guild_id
    )

    guild = bot.guilds[ctx.guild_id]
    guild.prefix = value

    await ctx.respond(f"Successfully updated message command prefix to `{value}`.")


@config.with_command
@tanjun.as_slash_command("list", "List the configurations for this guild.")
async def configure_list_cmd(
    ctx: tanjun.abc.SlashContext,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    assert ctx.guild_id is not None
    guild = await models.StarrGuild.from_db(bot.db, ctx.guild_id)
    name = g.name if (g := ctx.get_guild()) else "this guild"

    await ctx.respond(
        hikari.Embed(
            description=f"Configurations for {name}",
            color=hikari.Color(0x13F07A),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        .add_field("Starboard threshold:", f"`{guild.threshold}`", inline=True)
        .add_field("Starboard channel:", f"<#{guild.star_channel}>", inline=True)
        .add_field("Command Prefix:", f"`{guild.prefix}`", inline=False)
    )


########################################################################
# END CONFIG
########################################################################


@admin.with_command
@tanjun.with_str_slash_option("reason", "The optional reason to add to the audit log.", default="")
@tanjun.with_member_slash_option("member", "The member to kick.")
@tanjun.as_slash_command("kick", "Kick a member from the guild.", always_defer=True)
async def kick_slash_cmd(
    ctx: tanjun.abc.SlashContext,
    member: hikari.Member,
    reason: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    assert ctx.guild_id is not None

    try:
        await bot.rest.kick_member(ctx.guild_id, member, reason=reason)
    except hikari.ForbiddenError:
        await ctx.respond(
            f"Unable to kick <@!{member.id}>, I am missing permissions or my top role is too low."
        )
    else:
        await ctx.respond(f"Successfully kicked <@!{member.id}>.")


async def _ban_member(
    ctx: tanjun.abc.SlashContext,
    member: hikari.SnowflakeishOr[hikari.Member],
    reason: str,
    delete_message_days: int,
    bot: StarrBot,
) -> str:
    assert ctx.guild_id is not None
    member = member.id if isinstance(member, hikari.Member) else member

    try:
        await bot.rest.ban_member(
            ctx.guild_id,
            member,
            delete_message_days=delete_message_days,
            reason=reason + f" - banned by {ctx.author.username}",
        )
    except hikari.ForbiddenError:
        message = (
            f"Unable to ban <@!{member}>, I am missing permissions or my top role is too low."
        )

    else:
        message = f"Successfully banned <@!{member}>" + (
            f", and deleted their messages from the past {delete_message_days} days."
            if delete_message_days
            else "."
        )

    return message


@admin.with_command
@tanjun.with_int_slash_option(
    "delete_message_days",
    "The number of days to delete messages from this member.",
    default=0,
    min_value=0,
    max_value=7,
)
@tanjun.with_str_slash_option("reason", "The optional reason to add to the audit log.", default="")
@tanjun.with_member_slash_option("member", "The member to ban.")
@tanjun.as_slash_command("ban", "Ban a member from the guild.", always_defer=True)
async def ban_slash_cmd(
    ctx: tanjun.abc.SlashContext,
    member: hikari.Member,
    reason: str,
    delete_message_days: int,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    await ctx.respond(await _ban_member(ctx, member, reason, delete_message_days, bot))


@admin.with_command
@tanjun.with_int_slash_option(
    "delete_message_days",
    "The number of days to delete messages from this member.",
    default=0,
    min_value=0,
    max_value=7,
)
@tanjun.with_str_slash_option("reason", "The optional reason to add to the audit log.", default="")
@tanjun.with_member_slash_option("member", "The member to softban.")
@tanjun.as_slash_command(
    "softban", "Ban a member from the guild, and immediately unban them.", always_defer=True
)
async def softban_slash_cmd(
    ctx: tanjun.abc.SlashContext,
    member: hikari.Member,
    reason: str,
    delete_message_days: int,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    assert ctx.guild_id is not None

    message = await _ban_member(ctx, member, reason, delete_message_days, bot)
    await bot.rest.unban_member(
        ctx.guild_id, member, reason=f"softban release by {ctx.author.username}"
    )

    await ctx.respond(message.replace("banned", "softbanned"))


@admin.with_command
@tanjun.with_int_slash_option(
    "delete_message_days",
    "The number of days to delete messages from this member.",
    default=0,
    min_value=0,
    max_value=7,
)
@tanjun.with_str_slash_option("reason", "The optional reason to add to the audit log.", default="")
@tanjun.with_str_slash_option(
    "member", "The member to ban's Snowflake ID.", converters=tanjun.to_snowflake
)
@tanjun.as_slash_command("hackban", "Ban a member from the guild by ID.", always_defer=True)
async def hackban_slash_cmd(
    ctx: tanjun.abc.SlashContext,
    member: hikari.Snowflake,
    reason: str,
    delete_message_days: int,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    try:
        message = await _ban_member(ctx, member, reason, delete_message_days, bot)
    except hikari.NotFoundError:
        message = f"Hackban failed - invalid user ID: {member}."
    else:
        message = message.replace("banned", "hackbanned")

    await ctx.respond(message)


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(admin.copy())
