import hikari
from dotenv import load_dotenv

from starr import __version__, utils
from starr.bot import StarrBot


if __name__ == "__main__":
    load_dotenv()

    bot = StarrBot()
    utils.configure_logging()

    bot.run(
        activity=hikari.Activity(
            name=f"from the stars - v{__version__}",
            type=hikari.ActivityType.WATCHING,
        )
    )
