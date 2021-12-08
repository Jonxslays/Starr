import time as time

import hikari
import tanjun

from starr.bot import StarrBot


meta = tanjun.Component(name="meta").add_check(tanjun.checks.GuildCheck())


async def _ping(ctx: tanjun.abc.Context, bot: StarrBot) -> None:
    start = time.perf_counter()
    message = await ctx.respond("uwu-owo", ensure_result=True)
    elapsed = time.perf_counter() - start

    await message.edit(
        f"Gateway: {bot.heartbeat_latency * 1000:,.2f} ms\nRest: {elapsed * 1000:,.2f} ms"
    )


@meta.with_command
@tanjun.as_slash_command("ping", "Starr's latency.")
async def ping_slash_command(
    ctx: tanjun.abc.Context,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    await _ping(ctx, bot)


@meta.with_command
@tanjun.as_message_command("ping", "Starr's latency.")
async def ping_message_command(
    ctx: tanjun.abc.Context,
    bot: StarrBot = tanjun.inject(type=StarrBot),
) -> None:
    await _ping(ctx, bot)


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(meta.copy())
