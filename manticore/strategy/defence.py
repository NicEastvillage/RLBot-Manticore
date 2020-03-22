from gosling_utils.routines import goto_boost
from gosling_utils.utils import defaultPD, defaultThrottle, atba, argmin


class RotateOrDefendState:
    def __init__(self):
        pass

    def run(self, agent):
        if agent.me.boost < 20:
            # TODO Only do this when there are no threats
            big_pads = [pad for pad in agent.boosts if pad.large and pad.active]
            pad, _ = argmin(big_pads, lambda pad: pad.location.dist(agent.me.location)**0.5 + pad.location.dist(agent.friend_goal.location)**0.5)
            agent.push(goto_boost(pad, agent.friend_goal.location))
        else:
            dist_home = agent.me.location.dist(agent.friend_goal.location)
            if dist_home > 1400:
                atba(agent, agent.friend_goal.location, 2300)
            else:
                # Chill in goal area
                atba(agent, agent.ball.location, 100)
