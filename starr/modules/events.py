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
import lightbulb

from starr import utils

events = utils.Plugin("events")


def embedify(title: str, desc: str) -> hikari.Embed:
    return hikari.Embed(
        title=title,
        description=desc,
        color=hikari.Color(0xDB0000),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@events.listener(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    e = event.exception

    if isinstance(e, lightbulb.CommandNotFound):
        # Surpress command not found (how annoying)
        ...

    elif isinstance(e, lightbulb.NotEnoughArguments):
        missing = " ".join(f"<{m.name}>" for m in e.missing_options)
        await event.context.respond(
            embedify(
                "You forgot something...",
                f"These required arguments were missing: ```{missing}```",
            )
        )

    elif isinstance(e, lightbulb.MissingRequiredPermission):
        missing = ", ".join(str(p).replace("_", " ") for p in e.missing_perms)
        await event.context.respond(
            embedify(
                "You can't do that...",
                f"The following permissions are required: ```{missing}```",
            )
        )

    elif isinstance(e, lightbulb.ConverterFailure):
        await event.context.respond(embedify("That didn't go as planned...", f"```{e}```"))

    elif isinstance(e, lightbulb.NotOwner):
        await event.context.respond(
            embedify(
                "You can't do that...",
                f"Only Jon can run this command.",
            )
        )

    elif isinstance(e, lightbulb.CommandInvocationError):
        await event.context.respond(
            embedify(
                "This command is broken...",
                f"**{e.original.__class__.__name__}**: ```{e.original}```",
            )
        )

        raise e  # For logging

    else:
        await event.context.respond(
            embedify(
                "Uh oh, this ain't good...",
                f"**{e.__class__.__name__}**:\n```{e}```",
            )
        )

        raise e  # For logging


def load(app: lightbulb.BotApp) -> None:
    app.add_plugin(events)
