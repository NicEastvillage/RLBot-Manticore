from gosling_utils.routines import *
from gosling_utils.tools import *


class OffenceState:
    def __init__(self):
        pass

    def run(self, agent):
        targets = {"goal": (agent.foe_goal.left_post, agent.foe_goal.right_post)}
        shots = find_hits(agent, targets)
        if len(shots["goal"]) > 0:
            agent.push(shots["goal"][0])
        agent.push(short_shot(agent.foe_goal.location))
