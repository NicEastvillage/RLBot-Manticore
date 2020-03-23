from gosling_utils.routines import *
from gosling_utils.tools import *


class OffenceState:
    def __init__(self):
        pass

    def run(self, agent):
        # Reconsider ever 0.5 when far away
        if len(agent.stack) > 0:
            if agent.me.location.dist(agent.ball.location) > 1000 and agent.time % 0.5 == 0:
                agent.clear()

        if len(agent.stack) == 0:
            targets = {"goal": (agent.foe_goal.left_post, agent.foe_goal.right_post)}
            shots = find_hits(agent, targets)
            if len(shots["goal"]) > 0:
                agent.push(shots["goal"][0])
            else:
                agent.push(short_shot(agent.foe_goal.location))
