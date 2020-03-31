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
            # Count number of friends on the enemy side of the arena
            committed_friends = [friend for friend in agent.friends if friend.location.y * side(friend.team) < 0]
            many_committed_friends = len(committed_friends) <= len(agent.friends) / 2
            if side(agent.team) * (agent.me.location.y - agent.ball.location.y) > 0 and many_committed_friends:
                # Approach ball medium speed
                relative_target = agent.ball.location - agent.me.location
                local_target = agent.me.local(relative_target)
                defaultPD(agent, local_target)
                defaultThrottle(agent, max(agent.me.location.dist(agent.ball.location) / 3, 200))
            else:
                # We are on the wrong side of the ball
                relative_target = agent.friend_goal.location - agent.me.location
                local_target = agent.me.local(relative_target)
                defaultPD(agent, local_target)
                speed = 2300 if many_committed_friends else 1500
                defaultThrottle(agent, speed)
