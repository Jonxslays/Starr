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

# from __future__ import annotations

# import secrets

# import hikari
# import lightbulb
# import piston_rspy

# from starr import utils
# from starr.bot import StarrBot

# code = utils.Plugin("code", "Can you even program?")

# client = piston_rspy.Client()
# _runtimes: list[str] | None = None


# def filter_modal_interactions(
#     e: hikari.InteractionCreateEvent, ctx: utils.SlashContext, nonce: str
# ) -> bool:
#     # if not isinstance(e.interaction, hikari.ModalInteraction):
#     #     return False

#     # reveal_type(e.interaction)

#     return (
#         isinstance(e.interaction, hikari.ModalInteraction)
#         and e.interaction.user == ctx.author  # pyright: ignore
#         and e.interaction.custom_id == f"run-modal-{nonce}"  # pyright: ignore
#     )


# def wrap_result(text: str) -> str:
#     backtick = "`\u200b``"
#     return f"```sh\n{text.replace('```', backtick)}```"


# def build_response_embed(resp: piston_rspy.ExecResponse) -> hikari.Embed:
#     embed = hikari.Embed(
#         title=f"Executed your {resp.language} {resp.version} code",
#         timestamp=utils.now(),
#         color=0x14C41F,
#     )

#     if resp.is_err():
#         embed.description = f"Uh oh: {resp.status}"
#         embed.color = hikari.Color(0xE61E1E)
#         return embed

#     if resp.run.output:
#         if resp.run.is_err():
#             embed.color = hikari.Color(0xE61E1E)

#         run_output = resp.run.output

#         if len(run_output) >= 1014:
#             run_output = run_output[:1011] + "..."

#         result = wrap_result(run_output)
#     else:
#         result = wrap_result("No output")

#     if resp.compile:
#         if resp.compile.is_err():
#             compile_output = resp.compile.stderr

#             if len(compile_output) >= 1014:
#                 compile_output = compile_output[:1011] + "..."

#             embed.add_field("Compiler errors:", wrap_result(compile_output))
#             embed.color = hikari.Color(0xE61E1E)

#     embed.add_field("Output", result)
#     return embed


# async def handle_modal_responses(ctx: utils.SlashContext, language: str, nonce: str) -> None:
#     with ctx.bot.stream(hikari.InteractionCreateEvent, timeout=300).filter(
#         lambda e: filter_modal_interactions(e, ctx, nonce)
#     ) as stream:
#         async for event in stream:
#             inter = event.interaction
#             assert isinstance(inter, hikari.ModalInteraction)
#             await inter.create_initial_response(  # pyright: ignore
#                 hikari.ResponseType.DEFERRED_MESSAGE_CREATE
#             )

#             text: str = inter.components[0].components[0].value  # type: ignore
#             executor = piston_rspy.Executor(
#                 language=language.split(maxsplit=1)[0],
#                 files=[piston_rspy.File(content=text)],
#             )

#             response = await client.execute(executor)
#             embed = build_response_embed(response).set_author(
#                 name=ctx.author.username,
#                 icon=ctx.author.avatar_url or ctx.author.default_avatar_url,
#             )

#             await inter.edit_initial_response(embed)  # pyright: ignore
#             return None


# @code.command
# @lightbulb.set_help(docstring=True)
# @lightbulb.option("language", "The language to run.", autocomplete=True)
# @lightbulb.command("run", "Run some code.")
# @lightbulb.implements(lightbulb.SlashCommand)
# async def run_command(ctx: utils.SlashContext) -> None:
#     """Run some code in a language of your choice."""
#     nonce = secrets.token_hex(8)
#     language = ctx.options.language

#     components = (
#         ctx.bot.rest.build_action_row()
#         .add_text_input(f"run-input-{nonce}", "Add code here")
#         .set_style(hikari.TextInputStyle.PARAGRAPH)
#         .add_to_container()
#     )

#     if _runtimes and language not in _runtimes:
#         await ctx.interaction.create_initial_response(
#             hikari.ResponseType.MESSAGE_CREATE,
#             f"Oops, that was not a valid language.",
#             flags=hikari.MessageFlag.EPHEMERAL,
#         )
#         return None

#     await ctx.interaction.create_modal_response(
#         f"Running {language.split()[0]}"[:45], f"run-modal-{nonce}", (components,)
#     )

#     await handle_modal_responses(ctx, language, nonce)


# @run_command.autocomplete("language")
# async def run_autocomplete(
#     option: hikari.AutocompleteInteractionOption, _inter: hikari.AutocompleteInteraction
# ) -> tuple[str, ...]:
#     global _runtimes

#     if not _runtimes:
#         buffer = await client.fetch_runtimes()
#         pretty = tuple(f"{r.language.lower()} - v{r.version}" for r in buffer)
#         _runtimes = sorted(pretty)

#     assert isinstance(option.value, str)
#     return tuple(r for r in _runtimes if r.startswith(option.value.lower()))[:25]


# def load(bot: StarrBot) -> None:
#     bot.add_plugin(code)
