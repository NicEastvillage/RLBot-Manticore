from rlbot.agents.base_agent import SimpleControllerState

from util.rlmath import lerp
from util.vec import norm


class FollowUpState:
    def __init__(self):
        pass

    def exec(self, bot):
        return bot.drive.towards_point(
            bot,
            lerp(bot.info.ball.pos, bot.info.own_goal.pos, 0.5),
            target_vel=max(norm(bot.info.my_car.pos - bot.info.ball.pos) / 2, 800),
            slide=True,
            boost_min=0,
            can_keep_speed=False,
            can_dodge=True,
            wall_offset_allowed=125
        )
