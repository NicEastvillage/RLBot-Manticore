import math

from rlbot.agents.base_agent import SimpleControllerState

from maneuvers.maneuver import Maneuver
from util.info import GRAVITY, JUMP_MAX_DUR, JUMP_FORCE, THROTTLE_AIR_ACCEL, JUMP_ACCEL, JUMP_SPEED, BOOST_ACCEL, \
    BOOST_PR_SEC, MAX_SPEED
from util.rlmath import clip01
from util.vec import Vec3, norm, looking_in_dir, dot, angle_between, normalize


class Aerial(Maneuver):

    def __init__(self, bot, ball_location: Vec3, intercept_time: float, target: Vec3 = None):
        super().__init__()
        self.ball_location = ball_location
        self.intercept_time = intercept_time  # absolute time, e.g. 3m32s78ms
        self.target = target
        self.jumping = bot.on_ground
        self.time = -1
        self.jump_time = -1
        self.counter = 0

    def exec(self, bot):

        ct = bot.info.time
        car = bot.info.my_car
        controls = SimpleControllerState()

        if self.time == -1:
            elapsed = 0
            self.time = bot.info.time
        else:
            elapsed = bot.info.time - self.time

        T = self.intercept_time - bot.info.time
        xf = car.pos + car.vel * T + 0.5 * GRAVITY * T ** 2
        vf = car.vel + GRAVITY * T
        if self.jumping:
            if self.jump_time == -1:
                jump_elapsed = 0
                self.jump_time = ct
            else:
                jump_elapsed = ct - self.jump_time
            tau = JUMP_MAX_DUR - jump_elapsed
            if jump_elapsed == 0:
                vf += JUMP_FORCE
                xf += JUMP_FORCE * T

            vf += JUMP_FORCE * tau
            xf += JUMP_FORCE * tau * (T - 0.5 * tau)

            vf += JUMP_FORCE
            xf += JUMP_FORCE * (T - tau)

            if jump_elapsed < JUMP_MAX_DUR:
                controls.jump = True
            elif elapsed >= JUMP_MAX_DUR and self.counter < 3:
                controls.jump = False
                self.counter += 1
            elif elapsed < 0.3:
                controls.jump = True
            else:
                self.jumping = False
        else:
            car.controller.jump = 0

        delta_x = self.ball_location - xf
        direction = delta_x.normalize()
        if norm(delta_x) > 50:
            local_delta_x = dot(delta_x - car.pos, car.rot)
            pd = bot.fly.align(bot, looking_in_dir(local_delta_x))
        else:
            if self.target is not None:
                local_target = dot(self.target, car.rot)
                pd = bot.fly.align(bot, looking_in_dir(local_target))
            else:
                local_towards_ball = dot(self.ball_location - car.pos, car.rot)
                pd = bot.fly.align(bot, looking_in_dir(local_towards_ball))

        if JUMP_MAX_DUR <= elapsed < 0.3 and self.counter == 3:
            controls.roll = 0
            controls.pitch = 0
            controls.yaw = 0
        else:
            controls.roll = pd.roll
            controls.pitch = pd.pitch
            controls.yaw = pd.yaw

        if angle_between(car.forward, direction) < 0.3:
            if norm(delta_x) > 50:
                controls.boost = 1
                controls.throttle = 0
            else:
                controls.boost = 0
                controls.throttle = clip01(0.5 * THROTTLE_AIR_ACCEL * T ** 2)
        else:
            controls.boost = 0
            controls.throttle = 0

        self.done = T < 0  # TODO is ball where expect it to be?

        return controls

    def is_viable(self, car, time: float):
        T = self.intercept_time - time
        xf = car.pos + car.vel * T + 0.5 * GRAVITY * T ** 2
        vf = car.vel + GRAVITY * T
        if car.on_ground:
            vf += car.up * (2 * JUMP_SPEED + JUMP_ACCEL * JUMP_MAX_DUR)
            xf += car.up * (JUMP_SPEED * (2 * T - JUMP_MAX_DUR) + JUMP_ACCEL * (
                    T * JUMP_MAX_DUR - 0.5 * JUMP_MAX_DUR ** 2))

        delta_x = self.ball_location - xf
        dir = normalize(delta_x)
        phi = angle_between(dir, car.forward)
        turn_time = 0.7 * (2 * math.sqrt(phi / 9))

        tau1 = turn_time * clip01(1 - 0.3 / phi)
        required_acc = (2 * norm(delta_x)) / ((T - tau1) ** 2)
        ratio = required_acc / BOOST_ACCEL
        tau2 = T - (T - tau1) * math.sqrt(1 - clip01(ratio))
        velocity_estimate = vf + BOOST_ACCEL * (tau2 - tau1) * dir
        boost_estimate = (tau2 - tau1) * BOOST_PR_SEC
        enough_boost = boost_estimate < 0.95 * car.boost
        enough_time = abs(ratio) < 0.9
        return velocity_estimate.magnitude() < 0.9 * MAX_SPEED and enough_boost and enough_time
