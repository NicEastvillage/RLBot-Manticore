from gosling_utils.objects import *
from gosling_utils.routines import *


#This file is for strategy
from strategy.utility_system import UtilitySystem


class ExampleBot(GoslingAgent):
    def initialize_agent(self):
        super().initialize_agent()
        self.utility_system = UtilitySystem([
            AtbaState()
        ])

    def run(agent):
        if len(agent.stack) == 0 and agent.kickoff_flag:
            agent.push(kickoff())
        elif len(agent.stack) == 0:
            # We have nothing on stack. What to do?
            state = agent.utility_system.get_best_state(agent)
            state.run(agent)


class AtbaState:
    def utility_score(self, agent):
        return 0.1

    def run(self, agent):
        relative_target = agent.ball.location - agent.me.location
        local_target = agent.me.local(relative_target)
        defaultPD(agent, local_target)
        defaultThrottle(agent, 2300)
