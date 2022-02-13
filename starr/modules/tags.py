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

from starr import models
from starr import utils
from starr.bot import StarrBot

RESERVED_TAGS = (
    "create",
    "delete",
    "edit",
    "info",
    "list",
    "transfer",
    "claim",
    "alias",
)

tags_component = tanjun.Component(name="tags")


@tags_component.with_command
@tanjun.with_greedy_argument("name")
@tanjun.with_parser
@utils.with_help(
    "Get a tag or use a tag subcommand.",
    args=("name (str): The name of the tag or subcommand.",),
    usage="tag list\ntag jax is cute",
)
@tanjun.as_message_command_group("tag")
async def tag_group(
    ctx: tanjun.abc.MessageContext,
    name: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    query = (
        "UPDATE tags SET Uses = Uses + 1 WHERE GuildID = $1 AND TagName = $2 RETURNING TagContent;"
    )

    if content := await bot.db.fetch_one(query, ctx.guild_id, name.lower()):
        await ctx.respond(content)
        return None

    await ctx.respond(f"`{name}` is not a valid tag.")


@tag_group.with_command
@tanjun.with_greedy_argument("name")
@tanjun.with_parser
@utils.with_help(
    "Gets info about a tag.",
    args=("name (str): The name of the tag.",),
    usage="tag info my_tag\ntag info snab smort",
)
@tanjun.as_message_command("info")
async def tag_info_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
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
            description=f"Requested tag: `{name}`",
            color=hikari.Color(0x19FA3B),
        )
        .add_field("Owner", f"<@{tag_name_info[0]}>", inline=True)
        .add_field("Uses", tag_name_info[1], inline=True)
    )


@tag_group.with_command
@utils.with_help("List this guilds tags.", usage="tag list")
@tanjun.as_message_command("list")
async def tag_list_command(
    ctx: tanjun.abc.MessageContext,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    query = "SELECT TagName, TagOwner, Uses FROM tags WHERE GuildID = $1 ORDER BY Uses DESC;"
    tags = await bot.db.fetch_rows(query, ctx.guild_id)

    # If there are no tags stored
    if tags is None:
        await ctx.respond("No tags for this guild yet, make one!")
        return None

    # description: str = ", ".join(f"{t}" for t in tags)
    guild = ctx.get_guild()
    guild_name = guild.name if guild else "this guild"
    fields: list[tuple[str, ...]] = []

    for tag in tags:
        fields.append((tag[0], f"**Tag Owner**: <@{tag[1]}>\n**Tag Uses**: {tag[2]}"))

    pag = models.Paginator(
        ctx,
        bot,
        title=f"Tags for {guild_name}",
        description="",
        per_page=5,
        fields=fields,
    )
    await pag.paginate(60)


@tag_group.with_command
@tanjun.with_greedy_argument("content")
@tanjun.with_argument("name")
@tanjun.with_parser
@utils.with_help(
    "Create a new tag.",
    args=("name (str): The name of the tag.", "content (str): The tags content."),
    usage="tag create lol lul\ntag create beanos say wut :beanos:",
)
@tanjun.as_message_command("create")
async def tag_create_command(
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
            f"Sorry, `{name}` was already created by <@{owner}>. Try a different tag name.",
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

    await ctx.respond(f"`{name}` tag created by <@{ctx.author.id}>.")


@tag_group.with_command
@tanjun.with_greedy_argument("content")
@tanjun.with_argument("name")
@tanjun.with_parser
@utils.with_help(
    "Edit an existing tag you own.",
    args=("name (str): The name of the tag.", "content (str): The updated content."),
    usage="tag edit my_tag new content",
)
@tanjun.as_message_command("edit")
async def tag_edit_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
    content: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
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
        await ctx.respond(f"<@{owner}> owns the `{name}` tag, you cannot edit it.")
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
@utils.with_help(
    "Transfer a tag you own to another member.",
    args=("name (str): The name of the tag.", "member (int): The ID of the member to transer to."),
    usage="tag transfer my_tag 1234567898769420",
)
@tanjun.as_message_command("transfer")
async def tag_transfer_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
    member: int,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
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
            await ctx.respond(f"`{name}` tag transferred from <@{ctx.author.id}> to <@{member}>.")
            return None

        # Can't transfer a tag they don't own
        await ctx.respond(f"<@{owner}> owns the `{name}` tag, you cannot transfer it.")
        return None

    # Can't transfer a tag that doesn't exist
    await ctx.respond(f"No `{name}` tag exists to transfer.")


@tag_group.with_command
@tanjun.with_greedy_argument("name")
@tanjun.with_parser
@utils.with_help(
    "Delete a tag you own.",
    args=("name (str): The name of the tag.",),
    usage="tag delete my_tag",
)
@tanjun.as_message_command("delete")
async def tag_delete_command(
    ctx: tanjun.abc.MessageContext,
    name: str,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    assert ctx.guild_id is not None
    name = name.lower()

    select = "SELECT TagOwner FROM tags WHERE GuildID = $1 and TagName = $2;"
    delete = "DELETE FROM tags WHERE GuildID = $1 AND TagName = $2;"
    owner = await bot.db.fetch_one(select, ctx.guild_id, name)

    if not owner:
        # There is no tag with this name.
        await ctx.respond(f"Failed to delete tag `{name}`. It doesn't exist.")
        return None

    if not ctx.author.id == owner:
        # Fetch the member and permissions.
        member = await bot.rest.fetch_member(ctx.guild_id, ctx.author.id)
        permissions = await tanjun.utilities.fetch_permissions(ctx.client, member)

        if hikari.Permissions.ADMINISTRATOR in permissions:
            # Delete the tag, and announce admin perm usage.
            await bot.db.execute(delete, ctx.guild_id, name)
            await ctx.respond(
                f"<@{member.id}> deleted the `{name}` tag "
                f"(owned by <@{owner}>) using admin perms."
            )
            return None

        # They don't own the tag, and are not administrator.
        await ctx.respond(f"Failed to delete tag `{name}`. <@{owner}> owns it, not you.")
        return None

    # Successful deletion by the owner.
    await bot.db.fetch_one(delete, ctx.guild_id, name)
    await ctx.respond(f"`{name}` tag deleted by <@{ctx.author.id}>.")


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(tags_component.copy())
