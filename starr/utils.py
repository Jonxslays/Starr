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

import functools
import logging
import typing as t
from logging.handlers import RotatingFileHandler

import tanjun


def configure_logging() -> None:
    log = logging.getLogger("root")
    log.setLevel(logging.INFO)

    rfh = RotatingFileHandler(
        "./starr/data/logs/main.log",
        maxBytes=521288, # 512KB
        encoding="utf-8",
        backupCount=10,
    )

    ff = logging.Formatter(
        f"[%(asctime)s] %(levelname)s ||| %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    rfh.setFormatter(ff)
    log.addHandler(rfh)


def as_both_commands(
    component: tanjun.Component, *argv: t.Any, **kwargv: t.Any
)-> t.Callable[[t.Callable[..., t.Any]], tanjun.commands.BaseSlashCommand]:

    def inner(func: t.Callable[..., t.Any]) -> tanjun.commands.BaseSlashCommand:

        @component.with_command
        @tanjun.as_message_command(*argv, **kwargv)
        @functools.wraps(func)
        async def wrapper(
            *args: t.Any, **kwargs: t.Any
        ) -> t.Any:
            return await func(*args, **kwargs)

        return component.with_command(
            tanjun.as_slash_command(*argv, **kwargv)(wrapper)  # type: ignore
        )

    return inner
