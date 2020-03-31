from gosling_utils.objects import *
from gosling_utils.routines import *
from gosling_utils.tools import find_hits
from strategy.defence import RotateOrDefendState
from strategy.followup import FollowUpState
from strategy.offence import OffenceState

from strategy.utility_system import UtilitySystem, UtilityState


class ExampleBot(GoslingAgent):

    def initialize_agent(self):
        super().initialize_agent()
        self.states = {
            Objective.GO_FOR_IT: OffenceState(),
            Objective.FOLLOW_UP: FollowUpState(),
            Objective.ROTATE_BACK_OR_DEF: RotateOrDefendState()
        }

    def run(agent):

        agent.renderer.draw_string_3d(
            agent.me.location + Vector3(0, 0, 40),
            1, 1, str(agent.me.possession),
            agent.renderer.create_color(255, int((1 - agent.me.possession) * 150) + 105, int(agent.me.possession * 150) + 105, 40)
        )
        agent.renderer.draw_string_3d(
            agent.me.location + Vector3(0, 0, 90),
            1, 1, repr(agent.me.objective) + str(agent.me.onsite),
            agent.renderer.white()
        )

        if len(agent.stack) == 0 and agent.kickoff_flag:
            agent.push(kickoff())
        elif not agent.kickoff_flag:
            # Decide behaviour based on objective
            if agent.me.objective == Objective.UNKNOWN:
                print(f"Manticore {agent.index}: Unknown objective ?!?")
                atba(agent, agent.ball.location, 2000)
            else:
                agent.states[agent.me.objective].run(agent)
