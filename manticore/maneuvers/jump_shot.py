import math

from rlbot.agents.base_agent import SimpleControllerState

from maneuvers.maneuver import Maneuver
from util import predict, rendering
from util.info import GRAVITY, JUMP_MAX_DUR, THROTTLE_AIR_ACCEL, JUMP_ACCEL, JUMP_SPEED, BOOST_ACCEL, \
    BOOST_PR_SEC, MAX_SPEED
from util.rlmath import clip01, clip, lerp
from util.vec import Vec3, norm, looking_in_dir, dot, angle_between, normalize, Mat33


class JumpShotManeuver(Maneuver):

    def __init__(self, bot, ball_location: Vec3, intercept_time: float, do_second_jump: bool = False, target_rot: Mat33 = None):
        super().__init__()
        self.hit_pos = ball_location
        self.intercept_time = intercept_time  # absolute time, e.g. 3m32s78ms
        self.target_rot = target_rot
        self.jumping = bot.info.my_car.on_ground
        self.do_second_jump = do_second_jump
        self.do_dodge = not do_second_jump  # TODO
        self.jump_begin_time = -1
        self.jump_pause_counter = 0

    def exec(self, bot):

        ct = bot.info.time
        car = bot.info.my_car
        up = car.up
        controls = SimpleControllerState()

        # Time remaining till intercept time
        T = self.intercept_time - bot.info.time
        # Expected future position
        xf = car.pos + car.vel * T + 0.5 * GRAVITY * T ** 2
        # Expected future velocity
        vf = car.vel + GRAVITY * T

        # Set is set to false while jumping to avoid FeelsBackFlipMan
        rotate = True

        if self.jumping:
            if self.jump_begin_time == -1:
                jump_elapsed = 0
                self.jump_begin_time = ct
            else:
                jump_elapsed = ct - self.jump_begin_time

            # How much longer we can press jump and still gain upward force
            tau = JUMP_MAX_DUR - jump_elapsed

            # Add jump pulse
            if jump_elapsed == 0:
                vf += up * JUMP_SPEED
                xf += up * JUMP_SPEED * T
                rotate = False

            # Acceleration from holding jump
            vf += up * JUMP_SPEED * tau
            xf += up * JUMP_SPEED * tau * (T - 0.5 * tau)

            if self.do_second_jump:
                # Impulse from the second jump
                vf += up * JUMP_SPEED
                xf += up * JUMP_SPEED * (T - tau)

            if jump_elapsed < JUMP_MAX_DUR:
                controls.jump = True
            else:
                controls.jump = False
                if self.do_second_jump:
                    if self.jump_pause_counter < 4:
                        # Do a 4-tick pause between jumps
                        self.jump_pause_counter += 1
                    else:
                        # Time to start second jump
                        # we do this by resetting our jump counter and pretend and our aerial started in the air
                        self.jump_begin_time = -1
                        self.jumping = True
                        self.do_second_jump = False
                else:
                    # We are done jumping
                    self.jumping = False
        else:
            controls.jump = False

        delta_pos = self.hit_pos - xf
        direction = normalize(delta_pos)

        # We are not pressing jump, so let's orient the car
        if rotate:
            if norm(delta_pos) > 50:
                # local_delta_x = dot(delta_pos - car.pos, car.rot)  # FIXME Not sure if this needs to be local?
                pd = bot.fly.align(bot, looking_in_dir(delta_pos))
            else:
                if self.target_rot is not None:
                    pd = bot.fly.align(bot, self.target_rot)
                else:
                    pd = bot.fly.align(bot, looking_in_dir(self.hit_pos - car.pos))

            controls.roll = pd.roll
            controls.pitch = pd.pitch
            controls.yaw = pd.yaw

        if angle_between(car.forward, direction) < 0.3:
            if norm(delta_pos) > 50:
                controls.boost = 1
                controls.throttle = 0
            else:
                controls.boost = 0
                controls.throttle = clip01(0.5 * THROTTLE_AIR_ACCEL * T ** 2)
        else:
            controls.boost = 0
            controls.throttle = 0

        prediction = predict.ball_predict(bot, T)
        self.done = T < 0 or norm(self.hit_pos - prediction.pos) > 50

        if bot.do_rendering:
            car_to_hit_dir = normalize(self.hit_pos - car.pos)
            color = bot.renderer.pink()
            rendering.draw_cross(bot, self.hit_pos, color, arm_length=100)
            rendering.draw_circle(bot, lerp(car.pos, self.hit_pos, 0.25), car_to_hit_dir, 40, 12, color)
            rendering.draw_circle(bot, lerp(car.pos, self.hit_pos, 0.5), car_to_hit_dir, 40, 12, color)
            rendering.draw_circle(bot, lerp(car.pos, self.hit_pos, 0.75), car_to_hit_dir, 40, 12, color)
            bot.renderer.draw_line_3d(car.pos, self.hit_pos, color)

        return controls

    def is_viable(self, car, time: float):
        up = car.up
        T = self.intercept_time - time
        xf = car.pos + car.vel * T + 0.5 * GRAVITY * T ** 2
        vf = car.vel + GRAVITY * T

        if self.jumping:
            if self.jump_begin_time == -1:
                jump_elapsed = 0
                self.jump_begin_time = time
            else:
                jump_elapsed = time - self.jump_begin_time

            # How much longer we can press jump and still gain upward force
            tau = JUMP_MAX_DUR - jump_elapsed

            # Add jump pulse
            if jump_elapsed == 0:
                vf += up * JUMP_SPEED
                xf += up * JUMP_SPEED * T

            # Acceleration from holding jump
            vf += up * JUMP_SPEED * tau
            xf += up * JUMP_SPEED * tau * (T - 0.5 * tau)

            if self.do_second_jump:
                # Impulse from the second jump
                vf += up * JUMP_SPEED
                xf += up * JUMP_SPEED * (T - tau)

        delta_x = self.hit_pos - xf
        dir = normalize(delta_x)
        phi = angle_between(dir, car.forward)
        turn_time = 0.7 * (2 * math.sqrt(phi / 9))

        tau1 = turn_time * clip(1 - 0.3 / phi, 0.02, 1)
        required_acc = (2 * norm(delta_x)) / ((T - tau1) ** 2)
        ratio = required_acc / BOOST_ACCEL
        tau2 = T - (T - tau1) * math.sqrt(1 - clip01(ratio))
        velocity_estimate = vf + BOOST_ACCEL * (tau2 - tau1) * dir
        boost_estimate = (tau2 - tau1) * BOOST_PR_SEC
        enough_boost = boost_estimate < 0.95 * car.boost
        enough_time = abs(ratio) < 0.9
        return norm(velocity_estimate) < 0.9 * MAX_SPEED and enough_boost and enough_time
