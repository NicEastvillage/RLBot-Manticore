from gosling_utils.utils import defaultPD, defaultThrottle, side


class FollowUpState:
    def __init__(self):
        pass

    def run(self, agent):
        # Reconsider ever 0.5 when far away
        if len(agent.stack) > 0:
            if agent.me.location.dist(agent.ball.location) > 1400 and agent.time % 0.5 == 0:
                agent.clear()

        if len(agent.stack) == 0:
            if side(agent.team) * (agent.me.location.y - agent.ball.location.y) > 0:
                # Approach ball slowly
                relative_target = agent.ball.location - agent.me.location
                local_target = agent.me.local(relative_target)
                defaultPD(agent, local_target)
                defaultThrottle(agent, max(agent.me.location.dist(agent.ball.location) / 3, 200))
            else:
                # We are on the wrong side of the ball
                relative_target = agent.friend_goal.location - agent.me.location
                local_target = agent.me.local(relative_target)
                defaultPD(agent, local_target)
                defaultThrottle(agent, 1500)
