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

tags = utils.Plugin("tags", "Tag related commands.")


@tags.command
@lightbulb.set_help(docstring=True)
@lightbulb.option("name", "The name or alias of the tag to get.")
@lightbulb.command("tag", "Tag commands.")
@lightbulb.implements(lightbulb.PrefixCommandGroup)
async def tag_group(ctx: utils.PrefixContext) -> None:
    """Do tag things, like tell thommo he has a skill issue.

    Args:
        <name|subcommand>: The tag or subcommand to invoke.
    """
    name = ctx.options.name.lower()
    query = (
        "UPDATE tags SET uses = uses + 1 "
        "FROM tag_aliases a WHERE tags.guildid = $1 "
        "AND tags.tagname = $2 "
        "OR (a.tagalias = $2 AND tags.tagname = a.tagname) "
        "RETURNING tags.tagcontent;"
    )

    if content := await ctx.bot.db.fetch_one(query, ctx.guild_id, name):
        await ctx.respond(content)
        return None

    await ctx.respond(f"`{ctx.options.name}` is not a valid tag.")


@tag_group.child
@lightbulb.set_help(docstring=True)
@lightbulb.option("name", "The name of the tag.")
@lightbulb.command("info", "Get info about a tag.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_info_command(ctx: utils.PrefixContext) -> None:
    """Get info about a tag

    Args:
        <name|alias>: The tag name or alias to get info about.
    """
    name = ctx.options.name.lower()
    query = (
        "SELECT t.tagname, t.tagowner, t.uses "
        "FROM tags t FULL OUTER JOIN tag_aliases a "
        "ON t.tagname = a.tagname AND t.guildid = a.guildid "
        "WHERE t.guildid = $2 AND (t.tagname = $1 OR a.tagalias = $1) "
        "LIMIT 1;"
    )

    if not (tag_data := await ctx.bot.db.fetch_rows(query, name, ctx.guild_id)):
        await ctx.respond(f"No `{name}` tag exists.")
        return None

    new_name, owner, uses = tag_data[0]
    await ctx.respond(
        hikari.Embed(
            title=f"Tag information",
            description=f"Requested: `{name}` \nTag name: `{new_name}`",
            color=hikari.Color(0x19FA3B),
        )
        .add_field("Owner", f"<@{owner}>", inline=True)
        .add_field("Uses", uses, inline=True)
        .add_field("Is alias", str(new_name != name), inline=True)
    )


@tag_group.child
@lightbulb.set_help(docstring=True)
@lightbulb.command("list", "List this guilds tags.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_list_command(ctx: utils.PrefixContext) -> None:
    """List all of this guilds tags."""
    query = "SELECT TagName, TagOwner, Uses FROM tags WHERE GuildID = $1 ORDER BY Uses DESC;"
    tags = await ctx.bot.db.fetch_rows(query, ctx.guild_id)

    # If there are no tags stored
    if tags is None:
        await ctx.respond("No tags for this guild yet, make one!")
        return None

    guild = ctx.get_guild()
    guild_name = guild.name if guild else "this guild"
    fields: list[tuple[str, ...]] = []

    for tag in tags:
        fields.append((tag[0], f"Tag Owner: <@{tag[1]}>\nTag Uses: {tag[2]}"))

    pag = utils.Paginator(
        ctx,
        title=f"Tags for {guild_name}",
        description="",
        per_page=5,
        fields=fields,
    )
    await pag.paginate(60)


@tag_group.child
@lightbulb.set_help(docstring=True)
@lightbulb.option("alias", "The new alias for the tag.")
@lightbulb.option("name", "The name of the tag.")
@lightbulb.command("alias", "Set an alias on a tag.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_alias_command(ctx: utils.PrefixContext) -> None:
    """Set an alias for another tag.

    Args:
        <name>: The existing tag name.
        <alias>: The new alias to set for this tag.
    """
    name = ctx.options.name.lower()
    alias = ctx.options.alias.lower()

    # Can't alias a reserved tag
    if alias in RESERVED_TAGS:
        await ctx.respond(
            f"The following tag aliases are reserved: ```{', '.join(RESERVED_TAGS)}```",
        )
        return None

    if not (
        owner := await ctx.bot.db.fetch_one(
            "SELECT tagowner FROM tags WHERE guildid = $1 AND tagname = $2;", ctx.guild_id, name
        )
    ):
        # Probly a typo eh?
        await ctx.respond(f"Can't alias tag `{name}` because it does not exist, typo?.")
        return None

    if not ctx.author.id == owner:
        # The user doesn't own the tag, yikes
        await ctx.respond(f"<@{owner}> owns the `{name}` tag, so you can't alias it.")
        return None

    # They own the `name` tag, but does anyone have the alias
    if alias_owner := await ctx.bot.db.fetch_row(
        "SELECT t.tagowner FROM tags t FULL OUTER JOIN tag_aliases a "
        "ON t.tagname = a.tagname AND t.guildid = a.guildid "
        "WHERE t.guildid = $1 AND (t.tagname = $2 OR a.tagalias = $2)"
        "LIMIT 1;",
        ctx.guild_id,
        alias,
    ):
        # The alias is already in use, so we bail
        await ctx.respond(f"Sorry, `{alias}` is already in use by <@{alias_owner[0]}>.")
        return None

    # Create the alias
    await ctx.bot.db.fetch_one(
        "INSERT INTO tag_aliases (tagname, tagalias, guildid) VALUES ($1, $2, $3);",
        name,
        alias,
        ctx.guild_id,
    )
    await ctx.respond(f"Successfully aliased `{name}` to `{alias}`.")
    return None


@tag_group.child
@lightbulb.set_help(docstring=True)
@lightbulb.option("name", "The name of the tag.")
@lightbulb.command("claim", "Claim a tag from a user who left the server.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_claim_command(ctx: utils.PrefixContext) -> None:
    """Claim a tag from someone who left.

    Args:
        <name>: The name of the tag to claim.
    """
    name = ctx.options.name.lower()
    select = "SELECT tagowner FROM tags WHERE guildid = $1 AND tagname = $2;"
    transfer = "UPDATE tags SET tagowner = $1 WHERE guildid = $2 AND tagname = $3;"

    if not (owner := await ctx.bot.db.fetch_one(select, ctx.guild_id, name)):
        await ctx.respond(f"There is no tag named `{name}`, make it if you want it...")
        return None

    try:
        await ctx.bot.rest.fetch_member(ctx.guild_id, owner)
    except hikari.NotFoundError:
        # If we can't find the member, they aren't in the server
        await ctx.bot.db.execute(transfer, ctx.author.id, ctx.guild_id, name)
        await ctx.respond(f"Congrats, you own the `{name}` tag now!")
        return None

    # The tag owner is still in the server
    await ctx.respond(f"You can't have the `{name}` tag, <@{owner}> is still here!")


@tag_group.child
@lightbulb.set_help(docstring=True)
@lightbulb.option("content", "The tags content.", modifier=lightbulb.OptionModifier.CONSUME_REST)
@lightbulb.option("name", "The name of the tag.")
@lightbulb.command("create", "Create a new tag.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_create_command(ctx: utils.PrefixContext) -> None:
    """Create a new tag.

    Args:
        <name>: The new name for the tag.
        <content>: The content for the tag.
    """
    name = ctx.options.name.lower()
    content = ctx.options.content
    query = (
        "UPDATE tags SET uses = uses + 1 "
        "FROM tag_aliases a WHERE tags.guildid = $1 "
        "AND tags.tagname = $2 "
        "OR (a.tagalias = $2 AND tags.tagname = a.tagname) "
        "RETURNING tags.tagowner;"
    )

    # Can't create a reserved tag
    if name in RESERVED_TAGS:
        await ctx.respond(
            f"The following tag names are reserved: ```{', '.join(RESERVED_TAGS)}```",
        )
        return None

    # If they try to make an existing tag, yeah thats a use :kek:
    if owner := await ctx.bot.db.fetch_one(query, ctx.guild_id, name):
        await ctx.respond(
            f"Sorry, `{name}` was already created by <@{owner}>. Try a different tag name.",
        )
        return None

    # A successful tag creation
    await ctx.bot.db.execute(
        "INSERT INTO tags (GuildID, TagOwner, TagName, TagContent) VALUES ($1, $2, $3, $4);",
        ctx.guild_id,
        ctx.author.id,
        name,
        content,
    )

    await ctx.respond(f"`{name}` tag created by <@{ctx.author.id}>.")


@tag_group.child
@lightbulb.option(
    "content", "The updated content.", modifier=lightbulb.OptionModifier.CONSUME_REST
)
@lightbulb.option("name", "The name of the tag.")
@lightbulb.set_help(docstring=True)
@lightbulb.command("edit", "Edit a tag.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_edit_command(ctx: utils.PrefixContext) -> None:
    """Edit a tag you own.

    Args:
        <name>: The tag to edit.
        <content>: The new content for the tag.
    """
    name = ctx.options.name.lower()
    content = ctx.options.content
    query = (
        "SELECT t.tagowner FROM tags t FULL OUTER JOIN tag_aliases a "
        "ON t.tagname = a.tagname AND t.guildid = a.guildid "
        "WHERE t.guildid = $2 AND (t.tagname = $1 OR a.tagalias = $1) "
        "LIMIT 1;"
    )

    if owner := await ctx.bot.db.fetch_one(query, name, ctx.guild_id):
        # A successful tag edit
        if owner == ctx.author.id:
            await ctx.bot.db.execute(
                "UPDATE tags SET tagcontent = $1 WHERE tagname = $2 AND guildid = $3;",
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
    response = await ctx.respond(
        f"**WARNING**\nNo `{name}` tag exists to edit. Would you like to create it now?",
        component=(
            ctx.bot.rest.build_action_row()
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

    i_message = await response.message()

    # Stream interaction create events
    with ctx.bot.stream(hikari.InteractionCreateEvent, 30).filter(
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
                await ctx.bot.db.execute(
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


@tag_group.child
@lightbulb.set_help(docstring=True)
@lightbulb.option("user", "The name/ID of the user to transer to.", type=hikari.User)
@lightbulb.option("name", "The name of the tag.")
@lightbulb.command("transfer", "Transfer a tag to another user.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_transfer_command(ctx: utils.PrefixContext) -> None:
    """Transfer a tag to someone else.

    Args:
        <name>: The tag to transfer.
        <user>: The user to transfer to - in the form of:
         - User ID: 1234567890
         - Username: Jonxslays
            **Can fail if people have similar usernames**
         - Username#discrim: Jonxslays#0666
         - Mention: @Jonxslays
    """
    name = ctx.options.name.lower()
    user = ctx.options.user

    if owner := await ctx.bot.db.fetch_one(
        "SELECT TagOwner FROM tags WHERE GuildID = $1 AND TagName = $2;",
        ctx.guild_id,
        name,
    ):
        # A successful transfer
        if owner == ctx.author.id:
            await ctx.bot.db.execute(
                "UPDATE tags SET TagOwner = $1 WHERE GuildID = $2 AND TagName = $3;",
                user.id,
                ctx.guild_id,
                name,
            )
            await ctx.respond(f"`{name}` tag transferred from <@{ctx.author.id}> to <@{user.id}>.")
            return None

        # Can't transfer a tag they don't own
        await ctx.respond(f"<@{owner}> owns the `{name}` tag, you cannot transfer it.")
        return None

    # Can't transfer a tag that doesn't exist
    await ctx.respond(f"No `{name}` tag exists to transfer.")


@tag_group.child
@lightbulb.set_help(docstring=True)
@lightbulb.option("name", "The name of the tag.")
@lightbulb.command("delete", "Delete a tag.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def tag_delete_command(ctx: utils.PrefixContext) -> None:
    """Delete on of your tags.

    Args:
        <name>: The tag to delete.
    """
    name = ctx.options.name.lower()
    select = "SELECT tagowner FROM tags WHERE guildid = $1 and tagname = $2;"
    delete = "DELETE FROM tags WHERE guildid = $1 AND tagname = $2;"
    delete_aliases = "DELETE FROM tag_aliases WHERE guildid = $1 AND tagname = $2;"
    owner = await ctx.bot.db.fetch_one(select, ctx.guild_id, name)

    if not owner:
        # There is no tag with this name.
        await ctx.respond(f"Failed to delete tag `{name}`. It doesn't exist.")
        return None

    if not ctx.author.id == owner:
        # Fetch the member and permissions.
        member = await ctx.bot.rest.fetch_member(ctx.guild_id, ctx.author.id)
        permissions = lightbulb.utils.permissions_for(member)

        if hikari.Permissions.ADMINISTRATOR in permissions:
            # Delete the tag, and announce admin perm usage.
            await ctx.bot.db.execute(delete_aliases, ctx.guild_id, name)
            await ctx.bot.db.execute(delete, ctx.guild_id, name)
            await ctx.respond(
                f"<@{member.id}> deleted the `{name}` tag "
                f"(owned by <@{owner}>) using admin perms."
            )
            return None

        # They don't own the tag, and are not administrator.
        await ctx.respond(f"Failed to delete tag `{name}`. <@{owner}> owns it, not you.")
        return None

    # Successful deletion by the owner.
    await ctx.bot.db.execute(delete_aliases, ctx.guild_id, name)
    await ctx.bot.db.execute(delete, ctx.guild_id, name)
    await ctx.respond(f"`{name}` tag deleted by <@{ctx.author.id}>.")


def load(app: lightbulb.BotApp) -> None:
    app.add_plugin(tags)
