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

# import subprocess
# import sys

import tanjun

# from starr.bot import StarrBot

owner = tanjun.Component(name="owner").add_check(lambda ctx: ctx.author.id == 452940863052578816)


# class OutputCapture(list):
#     def __enter__(self):
#         self._stdout = sys.stdout



# @owner.with_command
# @tanjun.with_greedy_argument("source")
# @tanjun.as_message_command("eval")
# async def eval_cmd(
#     ctx: tanjun.abc.Context,
#     source: str,
#     bot: StarrBot = tanjun.inject(type=StarrBot),
# ) -> None:
#     lines = "".join(f"\n {l}" for l in source.split("\n"))
#     code = f"async def __lol(ctx, bot):{lines}"
#     exec(code, globals(), locals())

#     process = subprocess.call(["await", "locals()"])
#     returned = await locals()["__lol"](ctx, bot)

#     await ctx.respond(await locals()["__lol"](ctx, bot))


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(owner.copy())
