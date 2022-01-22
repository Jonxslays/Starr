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

import asyncio
import functools
import typing as t
from os import environ

import asyncpg


class Database:
    """Wrapper class for AsyncPG Database access."""

    def __init__(self) -> None:
        self.calls = 0
        self.db = environ["PG_DB"]
        self.host = environ["PG_HOST"]
        self.user = environ["PG_USER"]
        self.password = environ["PG_PASS"]
        self.port = environ["PG_PORT"]
        self.schema = "./starr/data/schema.sql"

    async def connect(self) -> None:
        """Opens a connection pool."""
        self.pool: asyncpg.Pool = await asyncpg.create_pool(
            user=self.user,
            host=self.host,
            port=self.port,
            database=self.db,
            password=self.password[0],
            loop=asyncio.get_running_loop(),
        )

        await self.scriptexec(self.schema)

    async def close(self) -> None:
        """Closes the connection pool."""
        await self.pool.close()

    @staticmethod
    def with_connection(func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        """A decorator used to acquire a connection from the pool."""

        @functools.wraps(func)
        async def wrapper(self: Database, *args: t.Any) -> t.Any:
            async with self.pool.acquire() as conn:
                self.calls += 1
                return await func(self, *args, conn=conn)

        return wrapper

    @with_connection
    async def fetch(self, q: str, *values: tuple[t.Any], conn: asyncpg.Connection) -> t.Any | None:
        """Read 1 field of applicable data."""
        query = await conn.prepare(q)
        return await query.fetchval(*values)

    @with_connection
    async def row(
        self, q: str, *values: t.Any, conn: asyncpg.Connection
    ) -> t.Optional[t.List[t.Any]]:
        """Read 1 row of applicable data."""
        query = await conn.prepare(q)
        if data := await query.fetchrow(*values):
            return [r for r in data]

        return None

    @with_connection
    async def rows(
        self, q: str, *values: t.Any, conn: asyncpg.Connection
    ) -> t.Optional[t.List[t.Iterable[t.Any]]]:
        """Read all rows of applicable data."""
        query = await conn.prepare(q)
        if data := await query.fetch(*values):
            return [*map(lambda r: tuple(r.values()), data)]

        return None

    @with_connection
    async def column(self, q: str, *values: t.Any, conn: asyncpg.Connection) -> t.List[t.Any]:
        """Read a single column of applicable data."""
        query = await conn.prepare(q)
        return [r[0] for r in await query.fetch(*values)]

    @with_connection
    async def execute(self, q: str, *values: t.Any, conn: asyncpg.Connection) -> None:
        """Execute a write operation on the database."""
        query = await conn.prepare(q)
        await query.fetch(*values)

    @with_connection
    async def executemany(
        self, q: str, values: t.List[t.Iterable[t.Any]], conn: asyncpg.Connection
    ) -> None:
        """Execute a write operation for each set of values."""
        query = await conn.prepare(q)
        await query.executemany(values)

    @with_connection
    async def scriptexec(self, path: str, conn: asyncpg.Connection) -> None:
        """Execute an sql script at a given path."""
        with open(path) as script:
            await conn.execute(script.read())
