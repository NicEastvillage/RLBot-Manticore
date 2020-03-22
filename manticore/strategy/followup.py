from gosling_utils.utils import defaultPD, defaultThrottle


class FollowUpState:
    def __init__(self):
        pass

    def run(self, agent):
        # Approach ball slowly
        relative_target = agent.ball.location - agent.me.location
        local_target = agent.me.local(relative_target)
        defaultPD(agent, local_target)
        defaultThrottle(agent, max(agent.me.location.dist(agent.ball.location) / 3, 200))
