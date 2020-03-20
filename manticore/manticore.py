from gosling_utils.objects import *
from gosling_utils.routines import *

from strategy.utility_system import UtilitySystem, UtilityState


class ExampleBot(GoslingAgent):

    def initialize_agent(self):
        super().initialize_agent()
        self.utility_system = UtilitySystem([
            AtbaState(),
            ShortShotState()
        ])

    def run(agent):
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


class ShortShotState(UtilityState):

    def utility_score(self, agent):
        ts = side(agent.me.team)
        if ts * agent.me.location.y < ts * agent.ball.location.y and agent.me.location.dist(agent.ball.location) < agent.foes[0].location.dist(agent.ball.location):
            return 0.5
        return 0

    def run(self, agent):
        agent.push(short_shot(agent.foe_goal.location))
