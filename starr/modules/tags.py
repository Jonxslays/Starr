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
import tanjun

from starr.bot import StarrBot

RESERVED_TAGS = (
    "create",
    "delete",
    "edit",
    "info",
    "list",
    "transfer",
)

tags_component = tanjun.Component(name="tags")


@tags_component.with_command
@tanjun.with_argument("name")
@tanjun.with_parser
@tanjun.as_message_command_group("tag")
async def tag_group(
    ctx: tanjun.abc.MessageContext,
    name: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    """Gets a tags content from the database."""
    query = (
        "UPDATE tags SET Uses = Uses + 1 WHERE GuildID = $1 AND TagName = $2 RETURNING TagContent;"
    )

    if content := await bot.db.fetch_one(query, ctx.guild_id, name.lower()):
        await ctx.respond(content)
        return None

    await ctx.respond(f"`{name}` is not a valid tag.")


@tag_group.with_command
@tanjun.with_argument("name")
@tanjun.with_parser
@tanjun.as_message_command("info")
async def tag_info_command(
    ctx: tanjun.abc.MessageContext,
    name:str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    """Gets info about a tag."""

    query = "SELECT TagOwner, Uses FROM tags WHERE TagName = $1 AND GuildID = $2;"

    if not (tag_name_info := await bot.db.fetch_row(query, name.lower(), ctx.guild_id)):
        await ctx.respond(f"No `{name}` tag exists.")
        return None

    await ctx.respond(
        hikari.Embed(
            title=f"Tag information",
            description=f"Requested tag: `{name}`" "",
            color=hikari.Color(0x19fa3b),
        )
        .add_field("Owner", f"<@!{tag_name_info[0]}>", inline=True)
        .add_field("Uses", tag_name_info[1], inline=True)
    )


@tag_group.with_command
@tanjun.as_message_command("list")
async def tag_list_command(
    ctx: tanjun.abc.MessageContext,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    """List this guilds tags."""
    query = "SELECT TagName FROM tags WHERE GuildID = $1;"
    tags = await bot.db.fetch_column(query, ctx.guild_id)

    # If there are no tags stored
    if not len(tags):
        await ctx.respond("No tags for this guild yet, make one!")
        return None

    description: str = ", ".join(f"{t}" for t in tags)
    guild = ctx.get_guild()
    guild_name = guild.name if guild else "this guild"

    await ctx.respond(
        hikari.Embed(
            title=f"Tags for {guild_name}",
            description=f"```{description}```",
            color=hikari.Color(0x19fa3b),
        )
    )


@tag_group.with_command
@tanjun.with_greedy_argument("content")
@tanjun.with_argument("name")
@tanjun.with_parser
@tanjun.as_message_command("create")
async def tag_create_slash_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
    content: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    """Create a new tag."""

    # Can't create a reserved tag
    if (name := name.lower()) in RESERVED_TAGS:
        await ctx.respond(
            f"The following tag names are reserved: ```{', '.join(RESERVED_TAGS)}```",
        )
        return None

    # If they try to make an existing tag, yeah thats a use :kek:
    if owner := await bot.db.fetch_one(
        "UPDATE tags SET Uses = Uses + 1 WHERE GuildID = $1 AND TagName = $2 RETURNING TagOwner;",
        ctx.guild_id,
        name,
    ):
        await ctx.respond(
            f"Sorry, `{name}` was already created by <@!{owner}>. Try a different tag name.",
        )
        return None

    # A successful tag creation
    await bot.db.execute(
        "INSERT INTO tags (GuildID, TagOwner, TagName, TagContent) VALUES ($1, $2, $3, $4);",
        ctx.guild_id,
        ctx.author.id,
        name,
        content,
    )

    await ctx.respond(f"`{name}` tag created by <@!{ctx.author.id}>.")


@tag_group.with_command
@tanjun.with_greedy_argument("content")
@tanjun.with_argument("name")
@tanjun.with_parser
@tanjun.as_message_command("edit",)
async def tag_edit_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
    content: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    """Edit an existing tag you own."""
    name = name.lower()

    if owner := await bot.db.fetch_one(
        "SELECT TagOwner FROM tags WHERE GuildID = $1 AND TagName = $2;", ctx.guild_id, name
    ):
        # A successful tag edit
        if owner == ctx.author.id:
            await bot.db.execute(
                "UPDATE tags SET TagContent = $1 WHERE TagName = $2 AND GuildID = $3;",
                content,
                name,
                ctx.guild_id,
            )
            await ctx.respond(f"`{name}` tag edited by {ctx.author.mention}.")
            return None

        # Author doesn't own the tag
        await ctx.respond(f"<@!{owner}> owns the `{name}` tag, you cannot edit it.")
        return None

    # There is no tag with that name, do they want to make one?
    i_message = await ctx.respond(
        f"**WARNING**\nNo `{name}` tag exists to edit. Would you like to create it now?",
        ensure_result=True,
        component=(
            ctx.rest.build_action_row()
            .add_button(
                hikari.ButtonStyle.SUCCESS,
                "yes",
            )
            .set_label("Yes")
            .add_to_container()
            .add_button(
                hikari.ButtonStyle.DANGER,
                "no",
            )
            .set_label("No")
            .add_to_container()
        ),
    )

    # Stream interaction create events
    with bot.stream(hikari.InteractionCreateEvent, 30).filter(
        # Filter out events that aren't our author and message
        lambda e: (
            isinstance(e.interaction, hikari.ComponentInteraction)
            and e.interaction.user == ctx.author
            and e.interaction.message == i_message
        )
    ) as stream:
        async for event in stream:
            assert isinstance(event.interaction, hikari.ComponentInteraction)

            if event.interaction.custom_id == "yes":
                await bot.db.execute(
                    "INSERT INTO tags (GuildID, TagOwner, TagName, TagContent) "
                    "VALUES ($1, $2, $3, $4);",
                    ctx.guild_id,
                    ctx.author.id,
                    name,
                    content,
                )
                await ctx.edit_last_response(
                    f"`{name}` tag created by {ctx.author.mention}.",
                    components=[],
                )
                return None

            elif event.interaction.custom_id == "no":
                await ctx.edit_last_response(f"Not creating new tag `{name}`.", components=[])
                return None

    await ctx.edit_last_response(f"No `{name}` tag exists to edit.", components=[])


@tag_group.with_command
@tanjun.with_argument("member", converters=int)
@tanjun.with_argument("name")
@tanjun.with_parser
@tanjun.as_message_command("transfer")
async def tag_transfer_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
    member: int,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    """Transfer a tag you own to another member."""
    name = name.lower()

    if owner := await bot.db.fetch_one(
        "SELECT TagOwner FROM tags WHERE GuildID = $1 AND TagName = $2;",
        ctx.guild_id,
        name,
    ):
        # A successful transfer
        if owner == ctx.author.id:
            await bot.db.execute(
                "UPDATE tags SET TagOwner = $1 WHERE GuildID = $2 AND TagName = $3;",
                member,
                ctx.guild_id,
                name,
            )
            await ctx.respond(
                f"`{name}` tag transferred from <@!{ctx.author.id}> to <@!{member}>."
            )
            return None

        # Can't transfer a tag they don't own
        await ctx.respond(f"<@!{owner}> owns the `{name}` tag, you cannot transfer it.")
        return None

    # Can't transfer a tag that doesn't exist
    await ctx.respond(f"No `{name}` tag exists to transfer.")


@tag_group.with_command
@tanjun.with_argument("name")
@tanjun.with_parser
@tanjun.as_message_command("delete")
async def tag_delete_slash_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    """Delete a tag you own."""
    name = name.lower()

    if owner := await bot.db.fetch_one(
        "SELECT TagOwner FROM tags WHERE GuildID = $1 AND TagName = $2;", ctx.guild_id, name
    ):
        # A successful deletion
        if owner == ctx.author.id:
            await bot.db.execute(
                "DELETE FROM tags WHERE GuildID = $1 AND TagName = $2;", ctx.guild_id, name
            )
            await ctx.respond(f"`{name}` tag deleted by <@!{ctx.author.id}>.")
            return None

        # Can't delete a tag they don't own
        await ctx.respond(f"<@!{owner}> owns the `{name}` tag, you cannot delete it.")
        return None

    # Can't delete a tag that doesn't exist
    await ctx.respond(f"No `{name}` tag exists to delete.")


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(tags_component.copy())
