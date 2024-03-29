from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats
from tmcp import TMCPHandler, TMCPMessage, TMCP_VERSION

from behaviour.carry import Carry
from behaviour.clear_ball import ClearBall
from behaviour.defend_goal import DefendGoal
from behaviour.follow_up import PrepareFollowUp
from behaviour.save_goal import SaveGoal
from behaviour.shoot_at_goal import ShootAtGoal
from controllers.drive import DriveController
from controllers.fly import FlyController
from controllers.other import celebrate
from controllers.shots import ShotController
from maneuvers.kickoff import choose_kickoff_maneuver
from strategy.analyzer import GameAnalyzer
from strategy.objective import Objective
from strategy.utility_system import UtilitySystem
from utility import draw
from utility.info import GameInfo, tcmp_to_quick_chat
from utility.vec import Vec3

RENDER = True


class Manticore(BaseAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.do_rendering = RENDER
        self.info = None
        self.ut = None
        self.analyzer = GameAnalyzer()
        self.choice = None
        self.maneuver = None
        self.doing_kickoff = False

        self.drive = DriveController()
        self.shoot = ShotController()
        self.fly = FlyController()

    def initialize_agent(self):
        self.info = GameInfo(self.index, self.team)
        self.ut = UtilitySystem([
            ShootAtGoal(),
            SaveGoal(self),
            ClearBall(self),
            Carry(),
            DefendGoal(),
            PrepareFollowUp()
        ])
        self.tmcp_handler = TMCPHandler(self)
        if TMCP_VERSION != [0, 9]:
            self.tmcp_handler.disable()
        if RENDER:
            draw.setup(self.renderer)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        # Read packet
        if not self.info.field_info_loaded:
            self.info.read_field_info(self.get_field_info())
            if not self.info.field_info_loaded:
                return SimpleControllerState()

        self.renderer.begin_rendering()

        self.info.read_packet(packet)
        self.handle_tmcp()
        self.analyzer.update(self)

        # Check if match is over
        if packet.game_info.is_match_ended:
            return celebrate(self)  # Assume we won!

        controller = self.use_brain()

        # Additional rendering
        doing = self.maneuver or self.choice
        state_color = {
            Objective.GO_FOR_IT: draw.lime(),
            Objective.FOLLOW_UP: draw.yellow(),
            Objective.ROTATING: draw.red(),
            Objective.SOLO: draw.team_color_sec(),
            Objective.UNKNOWN: draw.team_color_sec()
        }[self.info.my_car.objective]
        if doing is not None:
            draw.string_2d(330, 700 + self.index * 20, 1, f"{self.name}:", draw.team_color())
            draw.string_2d(500, 700 + self.index * 20, 1, doing.__class__.__name__, state_color)
            draw.rect_3d(self.info.my_car.pos + Vec3(z=60), 16, 16, state_color)
            draw.string_3d(self.info.my_car.pos + Vec3(z=110), 1, f"{self.info.my_car.last_ball_touch:.1f}", state_color)

        self.renderer.end_rendering()

        # Save some stuff for next tick
        self.feedback(controller)

        return controller

    def print(self, s):
        team_name = "[BLUE]" if self.team == 0 else "[ORANGE]"
        print("Manticore", self.index, team_name, ":", s)

    def feedback(self, controller):
        if controller is None:
            self.print(f"None controller from state: {self.info.my_car.objective} & {self.maneuver.__class__}")
        else:
            self.info.my_car.last_input.roll = controller.roll
            self.info.my_car.last_input.pitch = controller.pitch
            self.info.my_car.last_input.yaw = controller.yaw
            self.info.my_car.last_input.boost = controller.boost

    def handle_quick_chat(self, index, team, quick_chat):
        self.info.handle_quick_chat(index, team, quick_chat)

    def use_brain(self) -> SimpleControllerState:
        # Check kickoff
        if self.info.is_kickoff and not self.doing_kickoff:
            self.maneuver = choose_kickoff_maneuver(self)
            self.doing_kickoff = True
            self.print("Kickoff - Hello world!")

        # Execute logic
        if self.maneuver is None or self.maneuver.done:
            # There is no maneuver (anymore)
            self.maneuver = None
            self.doing_kickoff = False

            self.choice = self.ut.get_best_state(self)
            ctrl = self.choice.run(self)

            # The state has started a maneuver. Execute maneuver instead
            if self.maneuver is not None:
                return self.maneuver.exec(self)

            return ctrl

        return self.maneuver.exec(self)

    def handle_tmcp(self):
        """
        Receive and handle all match comms messages
        """
        new_messages = self.tmcp_handler.recv()
        for message in new_messages:
            self.info.handle_tmcp_message(message)

    def send_tmcp(self, message: TMCPMessage):
        """
        Send a TMCP message (and an equivalent quick chat message if possible)
        """
        self.tmcp_handler.send(message)
        # Transform message into quick chat message if we can
        qc_msg = tcmp_to_quick_chat(message.action_type)
        self.send_quick_chat(QuickChats.CHAT_EVERYONE, qc_msg)
