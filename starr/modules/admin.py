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
import lightbulb

from starr import utils
from starr.bot import StarrBot
from starr.models import StarrGuild

admin = utils.Plugin("admin", "Admin related commands.")
admin.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))


########################################################################
# START CONFIG
########################################################################


@admin.command
@lightbulb.set_help(docstring=True)
@lightbulb.command("config", "Starr configuration options.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def config_cmd(_: utils.SlashContext) -> None:
    """This command can only be used by administrators."""
    ...


@config_cmd.child
@lightbulb.option(
    "blacklist",
    "Adds a channel to the starboard blacklist.",
    type=hikari.TextableGuildChannel,
    channel_types=(hikari.ChannelType.GUILD_NEWS, hikari.ChannelType.GUILD_TEXT),
    default=None,
)
@lightbulb.option(
    "whitelist",
    "Adds a channel to the starboard whitelist.",
    type=hikari.TextableGuildChannel,
    channel_types=(hikari.ChannelType.GUILD_NEWS, hikari.ChannelType.GUILD_TEXT),
    default=None,
)
@lightbulb.option(
    "threshold",
    "Sets the number of stars a message must receive.",
    type=int,
    default=0,
    min_value=1,
)
@lightbulb.option(
    "channel",
    "Sets the starboard channel.",
    type=hikari.TextableGuildChannel,
    channel_types=(hikari.ChannelType.GUILD_TEXT,),
    default=None,
)
@lightbulb.command("starboard", "Configures the starboard for this guild.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def configure_starboard_cmd(ctx: utils.SlashContext) -> None:
    responses: list[str] = []
    blacklist = ctx.options.blacklist
    whitelist = ctx.options.whitelist
    threshold = ctx.options.threshold
    channel = ctx.options.channel
    guild = ctx.bot.guilds[ctx.guild_id]

    if channel:
        guild.star_channel = channel.id

        await ctx.bot.db.execute(
            "UPDATE guilds SET StarChannel = $1 WHERE GuildID = $2;",
            channel.id,
            ctx.guild_id,
        )
        responses.append(f"Successfully updated starboard channel to <#{channel.id}>.")

    if threshold:
        guild.threshold = threshold

        await ctx.bot.db.execute(
            "UPDATE guilds SET Threshold = $1 WHERE GuildID = $2;",
            threshold,
            ctx.guild_id,
        )
        responses.append(f"Successfully updated starboard star threshold to {threshold}.")

    if whitelist:
        await guild.remove_channel_from_blacklist(ctx.bot.db, whitelist.id)
        responses.append(f"Successfully whitelisted <#{whitelist.id}> for starboard activity.")

    if blacklist:
        await guild.add_channel_to_blacklist(ctx.bot.db, blacklist.id)
        responses.append(f"Successfully blacklisted <#{blacklist.id}> from starboard activity.")

    if responses:
        await ctx.respond("\n".join(responses))
    else:
        await ctx.respond("Nothing happened...")


@config_cmd.child
@lightbulb.option("value", "The new prefix to set.")
@lightbulb.command("prefix", "Configures command prefix for this guild.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def configure_prefix_cmd(ctx: utils.SlashContext) -> None:
    value = ctx.options.value

    await ctx.bot.db.execute(
        "UPDATE guilds SET Prefix = $1 WHERE GuildID = $2;", value, ctx.guild_id
    )

    guild = ctx.bot.guilds[ctx.guild_id]
    guild.prefix = value

    await ctx.respond(f"Successfully updated command prefix to `{value}`.")


@config_cmd.child
@lightbulb.command("list", "List the configurations for this guild.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def configure_list_cmd(ctx: utils.SlashContext) -> None:
    guild = await StarrGuild.from_db(ctx.bot.db, ctx.guild_id)
    name = g.name if (g := ctx.get_guild()) else "this guild"

    await ctx.respond(
        hikari.Embed(
            description=f"Configurations for {name}",
            color=hikari.Color(0x13F07A),
            timestamp=utils.now(),
        )
        .add_field("Starboard threshold:", f"`{guild.threshold}`", inline=True)
        .add_field("Starboard channel:", f"<#{guild.star_channel}>", inline=True)
        .add_field("Command Prefix:", f"`{guild.prefix}`", inline=False)
    )


def load(bot: StarrBot) -> None:
    bot.add_plugin(admin)
