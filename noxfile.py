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

from pathlib import Path

import nox
import toml


def get_dependencies() -> dict[str, str]:
    with open("pyproject.toml") as f:
        data = toml.loads(f.read())["tool"]["poetry"]
        deps = data["dev-dependencies"]
        deps.update(data["dependencies"])
        deps["hikari"] = deps["hikari"]["version"]

    return dict((k.lower(), f"{k}{v}") for k, v in deps.items())


DEPS = get_dependencies()


@nox.session(reuse_venv=True)
def types_mypy(session: nox.Session) -> None:
    session.install(
        "-U",
        DEPS["mypy"],
        DEPS["hikari"],
        DEPS["hikari-tanjun"],
        DEPS["python-dotenv"],
    )
    session.run("mypy", "starr")


@nox.session(reuse_venv=True)
def types_pyright(session: nox.Session) -> None:
    session.install(
        "-U",
        DEPS["pyright"],
        DEPS["hikari"],
        DEPS["hikari-tanjun"],
        DEPS["python-dotenv"],
    )
    session.run("pyright")


@nox.session(reuse_venv=True)
def formatting(session: nox.Session) -> None:
    session.install("-U", DEPS["black"], DEPS["len8"])
    session.run("black", ".", "--check")
    session.run("len8")


@nox.session(reuse_venv=True)
def imports(session: nox.Session) -> None:
    session.install("-U", DEPS["flake8"], DEPS["isort"])
    session.run("isort", "starr", "-cq")
    session.run(
        "flake8",
        "starr",
        "--select",
        "F4",
        "--extend-ignore",
        "E,F",
        "--extend-exclude",
        "__init__.py,",
    )


@nox.session(reuse_venv=True)
def licensing(session: nox.Session) -> None:
    missing: list[Path] = []
    files: list[Path] = [
        *Path("./starr").rglob("*.py"),
        *Path(".").glob("*.py"),
    ]

    for path in files:
        with open(path) as f:
            if "# Copyright (c)" not in f.readline():
                missing.append(path)

    if missing:
        formatted = "\n".join(f" - {m}" for m in missing)
        session.error(f"\nThe following files are missing their license:\n\n{formatted}")
