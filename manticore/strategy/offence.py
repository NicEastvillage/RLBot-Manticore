from gosling_utils.routines import *
from gosling_utils.tools import *


class OffenceState:
    def __init__(self):
        pass

    def run(self, agent):
        # Reconsider ever 0.5 when far away
        if len(agent.stack) > 0:
            if agent.me.location.dist(agent.ball.location) > 1400 and agent.time % 0.5 == 0:
                agent.clear()

        if len(agent.stack) == 0:
            if agent.ball.location.y * side(agent.team) > 0:
                # Ball is on our half
                targets = {"clear": (side(agent.team) * Vector3(-4100, 0, 0), side(agent.team) * Vector3(4100, 0, 0))}
                shots = find_hits(agent, targets)
                if len(shots["clear"]) > 0:
                    agent.push(shots["clear"][min(3, len(shots["clear"]) - 1)])
                else:
                    agent.push(short_shot(agent.foe_goal.location))
            else:
                targets = {"goal": (agent.foe_goal.left_post, agent.foe_goal.right_post)}
                shots = find_hits(agent, targets)
                if len(shots["goal"]) > 0:
                    agent.push(shots["goal"][min(3, len(shots["goal"]) - 1)])
                else:
                    agent.push(short_shot(agent.foe_goal.location))
