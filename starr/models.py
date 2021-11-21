from dataclasses import dataclass, field

from starr.db import Database


@dataclass(slots=True)
class StarrGuild:
    ident: int
    prefix: str
    star_channel: int | None = None


@dataclass(slots=True)
class GuildStore:
    data: dict[int, StarrGuild] = field(default_factory=dict)

    def get(self, ident: int) -> StarrGuild | None:
        return self.data.get(ident)

    def insert(self, ident: int, guild: StarrGuild) -> None:
        self.data[ident] = guild

    async def get_or_insert(self, ident: int, db: Database) -> StarrGuild:
        if not (starr_guild := self.get(ident)):
            guild, prefix, channel = await db.row(
                "INSERT INTO guilds (GuildID) VALUES ($1) "
                "RETURNING GuildID, Prefix, StarChannel;",
                ident,
            )

            starr_guild = StarrGuild(guild, prefix, channel)
            self.insert(ident, starr_guild)

        return starr_guild

    def __contains__(self, ident: int) -> bool:
        return ident in self.data
