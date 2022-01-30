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

from starr import utils

help_component = tanjun.Component(name="help")


@help_component.with_command
@tanjun.with_greedy_argument("command", default=None)
@tanjun.with_parser
@utils.with_help(
    "Get help with Starr's commands.",
    args=("command (str | None): Optional command to get help for.",),
    usage="help\nhelp tag",
)
@tanjun.as_message_command("help")
async def help_cmd(ctx: tanjun.abc.MessageContext, command: str | None) -> None:
    if not command:
        return await _default_help(ctx)

    await _command_help(ctx, command.lower())


async def _default_help(ctx: tanjun.abc.MessageContext) -> None:
    message_commands: list[tuple[str, ...]] = []

    for command in ctx.client.iter_message_commands():
        if isinstance(command, tanjun.MessageCommandGroup):
            message_commands.append(
                (
                    "|".join(command.names),
                    command.metadata["help"]
                    + f"\nSubcommands: {', '.join('|'.join(c.names) for c in command.commands)}",
                )
            )

        elif isinstance(command, tanjun.MessageCommand):
            message_commands.append(("|".join(command.names), command.metadata["help"]))

    message = " ----- Message Commands -----\n\n"
    message += "\n".join(f"{m[0]}\n - {m[1]}\n" for m in message_commands)

    await ctx.respond(
        hikari.Embed(
            title="Command help - for more info use help <command>",
            description=f"```{message}```",
            color=hikari.Color(0x1347F0),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
    )


async def _command_help(ctx: tanjun.abc.MessageContext, command: str) -> None:
    parts = command.split()
    cmds = list(filter(lambda c: parts[0] in c.names, ctx.client.iter_message_commands()))

    if not cmds:
        await ctx.respond(f"No command with name `{command}`.")
        return None

    final_command = cmds[0]

    if len(parts) > 1 and not isinstance(cmds[0], tanjun.MessageCommandGroup):
        await ctx.respond(f"`{cmds[0]}` is not a command group.")
        return None

    for i, part in enumerate(parts[1:]):
        if i >= len(cmds):
            await ctx.respond(f"No command with name `{command}`.")
            return None

        buffer = cmds[i]

        if isinstance(buffer, tanjun.MessageCommandGroup):
            subcmds = buffer.commands

            for subcmd in subcmds:
                if part in subcmd.names:
                    final_command = subcmd

        else:
            if part in buffer.names:
                final_command = buffer
            else:
                await ctx.respond(f"No command with name `{command}`.")
                return None

    args = final_command.metadata["args"]
    usage = final_command.metadata["usage"]

    await ctx.respond(
        hikari.Embed(
            title=f"Command help for {command}",
            color=hikari.Color(0x1347F0),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            description=final_command.metadata["help"],
        )
        .add_field("Args", f"```{args or None}```")
        .add_field("Usage", f"```{usage or 'No usage details.'}```")
    )


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(help_component.copy())
