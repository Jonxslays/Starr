import hikari

from starr.app import app


if __name__ == "__main__":
    app.run(
        activity=hikari.Activity(
            name="you, and counting stars!",
            type=hikari.ActivityType.PLAYING,
        )
    )
