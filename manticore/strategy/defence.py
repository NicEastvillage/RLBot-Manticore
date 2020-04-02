from gosling_utils.routines import goto_boost, short_shot
from gosling_utils.utils import defaultPD, defaultThrottle, do_atba, argmin


class RotateOrDefendState:
    def __init__(self):
        pass

    def run(self, agent):
        if len(agent.stack) > 0:
            if isinstance(agent.stack[-1], short_shot):
                if agent.me.location.dist(agent.ball.location) > 900:
                    agent.pop()

        if len(agent.stack) == 0:
            if agent.me.boost < 20:
                # TODO Only do this when there are no threats
                big_pads = [pad for pad in agent.boosts if pad.large and pad.active]
                pad, _ = argmin(big_pads, lambda pad: pad.location.dist(agent.me.location)**0.5 + pad.location.dist(agent.friend_goal.location)**0.5)
                agent.push(goto_boost(pad, agent.friend_goal.location))
            else:
                dist_home = agent.me.location.dist(agent.friend_goal.front_location)
                if dist_home > 1400:
                    do_atba(agent, agent.friend_goal.front_location, 2300)
                else:
                    # Chill in goal area
                    do_atba(agent, agent.ball.location, 300)
