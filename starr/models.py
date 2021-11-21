import datetime
import typing
from dataclasses import dataclass, field

import hikari

from starr.db import Database


@dataclass(slots=True)
class StarrGuild:
    guild_id: int
    prefix: str
    star_channel: int | None = None


@dataclass(slots=True)
class GuildStore:
    data: dict[int, StarrGuild] = field(default_factory=dict)

    def get(self, guild_id: int) -> StarrGuild | None:
        return self.data.get(guild_id)

    def insert(self, guild: StarrGuild) -> None:
        self.data[guild.guild_id] = guild

    async def get_or_insert(self, guild_id: int, db: Database) -> StarrGuild:
        if not (starr_guild := self.get(guild_id)):
            guild, prefix, channel = await db.row(
                "INSERT INTO guilds (GuildID) VALUES ($1) "
                "RETURNING GuildID, Prefix, StarChannel;",
                guild_id,
            )

            starr_guild = StarrGuild(guild, prefix, channel)
            self.insert(starr_guild)

        return starr_guild

    def __contains__(self, guild_id: int) -> bool:
        return guild_id in self.data


@dataclass(slots=True)
class Starrer:
    user_id: int
    reactions: list[hikari.Reaction] = field(default_factory=list)

    def sees_stars(self) -> bool:
        return bool(self.reactions)

    def add_star(self, reaction: hikari.Reaction) -> None:
        self.reactions.append(reaction)

    def rm_star(self, reaction: hikari.Reaction) -> None:
        for i, r in enumerate(self.reactions):
            if r.emoji == reaction.emoji:
                self.reactions.pop(i)


@dataclass(slots=True)
class StarMessage:
    message_id: int
    guild_id: int
    channel_id: int
    author_id: int
    timestamp: datetime.datetime
    content: str | None
    attachments: typing.Sequence[hikari.Attachment]
    embeds: typing.Sequence[hikari.Embed]
    reactions: typing.Sequence[hikari.Reaction]
    stickers: typing.Sequence[hikari.PartialSticker]
    starrers: dict[int, Starrer] = field(default_factory=dict)

    @classmethod
    def from_message(cls, message: hikari.Message) -> "StarMessage":
        assert message.guild_id is not None

        return cls(
            message_id=message.id,
            guild_id=message.guild_id,
            channel_id=message.channel_id,
            author_id=message.author.id,
            timestamp=message.timestamp,
            content=message.content,
            attachments=message.attachments,
            embeds=message.embeds,
            reactions=message.reactions,
            stickers=message.stickers,
        )


@dataclass(slots=True)
class Starboard:
    guild: StarrGuild
    messages: dict[int, StarMessage] = field(default_factory=dict)
