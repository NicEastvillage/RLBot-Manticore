from rlbot.agents.base_agent import SimpleControllerState


class RotateOrDefendState:
    def __init__(self):
        pass

    def exec(self, bot):
        return bot.drive.home(bot)
