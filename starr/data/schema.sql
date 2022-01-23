CREATE TABLE IF NOT EXISTS guilds (
    GuildID BIGINT NOT NULL PRIMARY KEY,
    Prefix TEXT DEFAULT './',
    StarChannel BIGINT DEFAULT 0,
    StarsConfigured INT DEFAULT 0,
    Threshold INT DEFAULT 5
);

CREATE TABLE IF NOT EXISTS starboard_messages (
    StarMessageID BIGINT NOT NULL PRIMARY KEY,
    ReferenceID BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    GuildID bigint,
    TagOwner bigint,
    TagName text,
    TagContent text,
    Uses bigint DEFAULT 0,
    PRIMARY KEY (GuildID, TagName)
);
