from rlbot.agents.base_agent import SimpleControllerState


class OffenceState:
    def __init__(self):
        pass

    def exec(self, bot):
        return bot.drive.towards_point(
            bot,
            bot.info.ball.pos,
            target_vel=2300,
            slide=False,
            boost_min=0,
            can_keep_speed=True,
            can_dodge=True,
            wall_offset_allowed=125
        )
