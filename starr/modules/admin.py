import hikari
import tanjun

from starr.bot import StarrBot


admin = (
    tanjun.Component(name="admin")
    .add_check(tanjun.checks.GuildCheck())
    .add_check(tanjun.checks.AuthorPermissionCheck(hikari.Permissions.ADMINISTRATOR))
)


@tanjun.as_loader
def load_component(client: tanjun.Client) -> None:
    client.add_component(admin.copy())
