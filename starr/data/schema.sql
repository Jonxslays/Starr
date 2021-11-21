CREATE TABLE IF NOT EXISTS guilds (
    GuildID bigint NOT NULL PRIMARY KEY,
    Prefix text DEFAULT '$',
    StarChannel bigint DEFAULT 0
);
