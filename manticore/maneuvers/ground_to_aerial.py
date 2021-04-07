import math
from typing import Tuple

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.structures.quick_chats import QuickChats
from tmcp import TMCPMessage

from controllers.other import turn_radius
from maneuvers.aerial import AerialManeuver
from maneuvers.maneuver import Maneuver
from utility import predict, rendering
from utility.curves import curve_from_arrival_dir
from utility.predict import DummyObject
from utility.rendering import draw_bezier
from utility.rlmath import sign, lerp
from utility.vec import Vec3, rotate2d, dot, inv, norm, normalize, xy, axis_to_rotation


class GroundToAerial(Maneuver):
    def __init__(self, ball_hit_pos, hit_time):
        super().__init__()
        self.ball_hit_pos = ball_hit_pos
        self.hit_time = hit_time
        self.aerial = AerialManeuver(ball_hit_pos, hit_time, True)
        self.has_started_aerial = False
        self.take_off_time = -1
        self.take_off_spot = Vec3()
        self.announced_in_tmcp = False

    def exec(self, bot) -> SimpleControllerState:

        T = self.hit_time - bot.info.time
        car = bot.info.my_car

        if not self.announced_in_tmcp:
            self.announced_in_tmcp = True
            bot.send_tmcp(TMCPMessage.ball_action(bot.team, bot.index, self.hit_time))

        if self.take_off_time == -1:
            self.done = not self.is_viable(bot, bot.info.my_car, bot.info.time)

        if bot.info.time >= self.take_off_time:
            self.has_started_aerial = True

        if self.has_started_aerial:
            controls = self.aerial.exec(bot)
            self.done = self.aerial.done
            return controls

        car_to_ball_xy = xy(self.ball_hit_pos - car.pos)
        speed = norm(car_to_ball_xy) / T
        if speed > 2400:
            # We can't go that fast
            self.done = True

        controls = bot.drive.towards_point(bot, xy(self.ball_hit_pos), target_vel=speed, slide=True, boost_min=10, can_keep_speed=False, can_dodge=False)

        prediction = predict.ball_predict(bot, T)
        self.done = T < 0
        if norm(self.ball_hit_pos - prediction.pos) < 50:
            # Adjust hit pos
            self.ball_hit_pos = prediction.pos
        else:
            # Jump shot failed
            self.done = True
            bot.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Apologies_Cursing)

        return controls

    def is_viable(self, bot, car, current_time) -> bool:
        if self.has_started_aerial:
            return self.aerial.is_viable(car, car.rot, car.boost, current_time)

        rend = bot.renderer

        car_to_hit_pos = self.ball_hit_pos - car.pos

        # Boost FIXME: Does not consider required speed increase
        boost_req = (max(0, self.ball_hit_pos.z - 300) ** 1.1) / 30
        if car.boost < boost_req:
            return False

        # Velocity
        avg_vel_needed = norm(car_to_hit_pos) / self.hit_time
        if avg_vel_needed > 2250:
            return False
        current_vel_towards_hit = dot(car.vel, normalize(xy(car_to_hit_pos)))
        if current_vel_towards_hit < 200:
            return False
        current_vel_forwards = dot(car.vel, car.forward)
        vel_diff = avg_vel_needed - lerp(current_vel_towards_hit, current_vel_forwards, 0.5)
        if vel_diff < 0:
            # We need to break
            vel_adj_t = vel_diff / -3500
        else:
            # We need to speed up. This acceleration is an estimate.
            # See https://samuelpmish.github.io/notes/RocketLeague/ground_control/#throttle
            vel_adj_t = vel_diff / 1010

        # Angle
        hit_pos_local = dot(self.ball_hit_pos - car.pos, car.rot)
        angle2d = math.atan2(hit_pos_local.y, hit_pos_local.x)
        if abs(angle2d) > 0.45 * math.pi:
            return False
        vf = dot(car.forward, car.vel)
        ang_adj_t, offset = time_and_offset_to_turn(angle2d, vf)
        new_pos = car.pos + dot(offset, inv(car.rot))
        new_forward = rotate2d(car.forward, angle2d)
        new_rot = dot(axis_to_rotation(Vec3(z=angle2d)), car.rot)

        # Render new position/rotation
        rend.draw_line_3d(new_pos, new_pos + new_rot.forward * 50, rend.red())
        rend.draw_line_3d(new_pos, new_pos + new_rot.left * 50, rend.blue())
        rend.draw_line_3d(new_pos, new_pos + new_rot.up * 50, rend.green())

        # Find take-off pos
        z = self.ball_hit_pos.z
        if z < 300:
            return False
        min_take_off_dist = (2 - math.exp(-z / 1400)) * z + 140
        ball_to_new_car_pos = new_pos - self.ball_hit_pos
        ball_to_new_car_pos_2d_u = normalize(xy(ball_to_new_car_pos))
        ball_to_new_car_pos_2d_dist = norm(xy(ball_to_new_car_pos))
        if ball_to_new_car_pos_2d_dist < min_take_off_dist:
            return False
        ideal_take_off_pos = xy(self.ball_hit_pos) + ball_to_new_car_pos_2d_u * min_take_off_dist + Vec3(z=18)  # + Car height

        dist_to_take_off_pos = norm(new_pos - ideal_take_off_pos)
        if dist_to_take_off_pos > 800:
            return False
        time_to_reach_take_off = dist_to_take_off_pos / avg_vel_needed

        mid_point = curve_from_arrival_dir(car.pos, new_pos, ball_to_new_car_pos_2d_u)
        rend.draw_line_3d(car.pos, new_pos, rend.green())
        rendering.draw_bezier(bot, [car.pos, mid_point, new_pos], time_step=0.1)
        rend.draw_line_3d(new_pos, ideal_take_off_pos, rend.green())
        rend.draw_line_3d(ideal_take_off_pos, self.ball_hit_pos, rend.pink())

        # Result
        adj_time = max(vel_adj_t, ang_adj_t) + time_to_reach_take_off
        new_vel = avg_vel_needed * new_forward * 0.9
        obj = DummyObject()
        obj.pos = ideal_take_off_pos
        obj.vel = new_vel
        # FIXME is the aerial viable?
        self.take_off_time = current_time + adj_time
        self.take_off_spot = ideal_take_off_pos
        return True


    @staticmethod
    def test(bot):
        if bot.index == 0:
            # for t in range(1, 12):
            #     t = t / 4.0

            t = predict.time_till_reach_ball(bot.info.my_car, bot.info.ball)
            obj = predict.ball_predict(bot, t)
            viable = GroundToAerial(obj.pos, t).is_viable(bot, bot.info.my_car, bot.info.time)
            color = bot.renderer.yellow() if viable else bot.renderer.red()
            rendering.draw_cross(bot, obj.pos, color, 70)


def time_and_offset_to_turn(angle: float, vf: float) -> Tuple[float, Vec3]:
    """
    Calculates how long it will take to turn an amount of radius assuming we are driving on the ground
    with a constant forward velocity. Specifically, this returns how long it will take to adjust the
    forward vector with the given amount of degrees (in radians, pos/neg=right/left). Turning requires moving,
    so additionally, the local translation that the car will make in the XY plane is returned as well.
    """
    vf = max(vf, 300)
    dir = sign(angle)
    radius = turn_radius(vf)
    curve_dist = radius * angle
    time = curve_dist / vf
    offset = rotate2d(Vec3(y=-dir * radius), angle) + Vec3(y=dir * radius)
    return time, offset
