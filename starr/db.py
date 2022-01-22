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
