from strategy.objective import Objective
from utility import predict, rendering
from utility.rlmath import argmin, argmax, clip01
from utility.vec import Vec3, xy
from utility.vec import norm, normalize, dot


class GameAnalyzer:
    def __init__(self):
        self.opp_closest_to_ball = None
        self.opp_closest_to_ball_dist = 99999
        self.car_with_possession = None
        self.ally_with_possession = None
        self.opp_with_possession = None
        self.first_to_reach_ball = None
        self.ideal_follow_up_pos = Vec3()

    def update(self, bot):
        ball = bot.info.ball

        # Find closest foe to ball
        self.opp_closest_to_ball, self.opp_closest_to_ball_dist = argmin(bot.info.opponents, lambda opp: norm(opp.pos - ball.pos))

        # Possession and on/off-site
        self.car_with_possession = None
        self.ally_with_possession = None
        self.opp_with_possession = None
        for car in bot.info.cars:

            # On site
            own_goal = bot.info.goals[car.team]
            ball_to_goal = own_goal.pos - ball.pos
            car_to_ball = ball.pos - car.pos
            car.onsite = dot(ball_to_goal, car_to_ball) < 0.1

            # Reach ball time
            car.reach_ball_time = predict.time_till_reach_ball(car, ball)
            reach01 = clip01((5 - car.reach_ball_time) / 5)

            # Possession
            point_in_front = car.pos + car.vel * 0.6
            ball_point_dist = norm(ball.pos - point_in_front)
            dist01 = 1500 / (1500 + ball_point_dist)  # Halves every 1500 uu of dist
            car_to_ball = bot.info.ball.pos - car.pos
            car_to_ball_unit = normalize(car_to_ball)
            in_front01 = dot(car.forward, car_to_ball_unit) if car.on_ground else 0.5
            car.possession = dist01 * in_front01 * reach01 * 3
            if self.car_with_possession is None or car.possession > self.car_with_possession.possession:
                self.car_with_possession = car
            if car.team == bot.team and (self.ally_with_possession is None or car.possession > self.ally_with_possession.possession):
                self.ally_with_possession = car
            if car.team != bot.team and (self.opp_with_possession is None or car.possession > self.opp_with_possession.possession):
                self.opp_with_possession = car

        # Objectives
        for car in bot.info.cars:
            car.last_objective = car.objective
            car.objective = Objective.UNKNOWN
        thirdman_index, _ = argmin(bot.info.team_cars, lambda ally: norm(ally.pos - bot.info.own_goal.pos))
        attacker, attacker_score = argmax(bot.info.team_cars,
                                          lambda ally: ((0.09 if ally.last_objective == Objective.GO_FOR_IT else 0)
                                                        + ally.boost / 490
                                                        - (0.21 if ally.index == thirdman_index else 0)
                                                        - (0.4 if not ally.onsite else 0)
                                                        + ally.possession * (10_000 - ally.team_sign * ally.pos.y) / 20_000)**2)
        attacker.objective = Objective.GO_FOR_IT
        self.ideal_follow_up_pos = xy(ball.pos + bot.info.own_goal.pos) * 0.5 + Vec3(x=-min(ball.pos.x, 3000))
        if bot.do_rendering:
            bot.renderer.begin_rendering()
            rendering.draw_cross(bot, self.ideal_follow_up_pos, bot.renderer.team_color(), 80)
            rendering.draw_circle(bot, self.ideal_follow_up_pos, Vec3(z=1), 85, 20, bot.renderer.team_color())
            bot.renderer.draw_line_3d(bot.info.my_car.pos, self.ideal_follow_up_pos, bot.renderer.team_color())
        follower, follower_score = argmin([ally for ally in bot.info.team_cars if ally.objective == Objective.UNKNOWN],
                                          lambda ally: (-500 if ally.last_objective == Objective.FOLLOW_UP else 0)
                                                        - ally.boost * 2
                                                        + (1100 if ally.index == thirdman_index else 0)
                                                        + (400 if not ally.onsite else 0)
                                                        + norm(ally.pos - self.ideal_follow_up_pos))
        if follower is not None:
            follower.objective = Objective.FOLLOW_UP
        for car in bot.info.team_cars:
            if car.objective == Objective.UNKNOWN:
                car.objective = Objective.ROTATE_BACK_OR_DEF
