from gosling_utils.objects import *
from gosling_utils.routines import *
from gosling_utils.tools import find_hits

from strategy.utility_system import UtilitySystem, UtilityState


class ExampleBot(GoslingAgent):

    def initialize_agent(self):
        super().initialize_agent()
        self.utility_system = UtilitySystem([
            OffensiveCommit(),
            ApproachBallSlowly(),
            FallBack(),
            AtbaState()
        ])

    def run(agent):
        if agent.team == 0:
            agent.renderer.draw_string_3d(
                agent.me.location + Vector3(0, 0, 40),
                1, 1, str(agent.me.possession),
                agent.renderer.create_color(255, int((1 - agent.me.possession) * 150) + 105, int(agent.me.possession * 150) + 105, 40)
            )
            agent.renderer.draw_string_3d(
                agent.me.location + Vector3(0, 0, 90),
                1, 1, repr(agent.me.objective),
                agent.renderer.white()
            )

        if len(agent.stack) == 0 and agent.kickoff_flag:
            agent.push(kickoff())
        elif len(agent.stack) == 0:
            # We have nothing on stack. What to do?
            state = agent.utility_system.get_best_state(agent)
            state.run(agent)


# Mostly an edge case fallback state
class AtbaState(UtilityState):

    def utility_score(self, agent):
        return 0.1

    def run(self, agent):
        relative_target = agent.ball.location - agent.me.location
        local_target = agent.me.local(relative_target)
        defaultPD(agent, local_target)
        defaultThrottle(agent, 2300)


class OffensiveCommit(UtilityState):
    def utility_score(self, agent):
        if agent.me.objective == Objective.GO_FOR_IT:
            return agent.me.possession * 1.1
        if agent.me.objective == Objective.FOLLOW_UP:
            return agent.me.possession * 0.9
        return 0

    def run(self, agent):
        targets = {"goal": (agent.foe_goal.left_post, agent.foe_goal.right_post)}
        shots = find_hits(agent, targets)
        if len(shots["goal"]) > 0:
            agent.push(shots["goal"][0])
        agent.push(short_shot(agent.foe_goal.location))


class ApproachBallSlowly(UtilityState):
    def utility_score(self, agent):
        if agent.me.objective == Objective.FOLLOW_UP:
            return 0.75 - agent.me.possession
        return 0

    def run(self, agent):
        relative_target = agent.ball.location - agent.me.location
        local_target = agent.me.local(relative_target)
        defaultPD(agent, local_target)
        defaultThrottle(agent, 1000)


class FallBack(UtilityState):
    def utility_score(self, agent):
        if agent.me.objective == Objective.ROTATE_BACK_OR_DEF:
            return 0.75
        return 0

    def run(self, agent):
        # TODO Consider boost pickup
        relative_target = agent.friend_goal.location - agent.me.location
        local_target = agent.me.local(relative_target)
        defaultPD(agent, local_target)
        defaultThrottle(agent, 2300)
