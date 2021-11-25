import dotenv
import hikari

from starr.bot import StarrBot


if __name__ == "__main__":
    dotenv.load_dotenv()

    bot = StarrBot()
    bot.run(
        activity=hikari.Activity(
            name="for stars!",
            type=hikari.ActivityType.WATCHING,
        )
    )
