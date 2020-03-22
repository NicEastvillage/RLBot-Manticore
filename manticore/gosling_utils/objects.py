import math
import rlbot.utils.structures.game_data_struct as game_data_struct
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState

#This file holds all of the objects used in gosling utils
#Includes custom vector and matrix objects
from gosling_utils.vec import Vector3, Matrix3
from strategy.analyzer import GameAnalyzer, Objective


class GoslingAgent(BaseAgent):
    #This is the main object of Gosling Utils. It holds/updates information about the game and runs routines
    #All utils rely on information being structured and accessed the same way as configured in this class
    def initialize_agent(self):
        #A list of cars for both teammates and opponents
        self.all_cars = []
        self.friends = []
        self.foes = []
        #This holds the carobject for our agent
        self.me = car_object(self.index)
        
        self.ball = ball_object()
        self.game = game_object()
        #A list of boosts
        self.boosts = []
        #goals
        self.friend_goal = goal_object(self.team)
        self.foe_goal = goal_object(not self.team)
        #A list that acts as the routines stack
        self.stack = []
        #Game time
        self.time = 0.0
        #Whether or not GoslingAgent has run its get_ready() function
        self.ready = False
        #the controller that is returned to the framework after every tick
        self.controller = SimpleControllerState()
        #a flag that tells us when kickoff is happening
        self.kickoff_flag = False

        self.last_time = 0
        self.my_score = 0
        self.foe_score = 0

        self.analysis = GameAnalyzer()
        
    def get_ready(self,packet):
        #Preps all of the objects that will be updated during play
        field_info = self.get_field_info()
        for i in range(field_info.num_boosts):
            boost = field_info.boost_pads[i]
            self.boosts.append(boost_object(i,boost.location,boost.is_full_boost))
        self.refresh_player_lists(packet)
        self.ball.update(packet)
        self.ready = True
    def refresh_player_lists(self,packet):
        #makes new freind/foe/all lists
        #Useful to keep separate from get_ready because humans can join/leave a match
        self.friends = [car_object(i,packet) for i in range(packet.num_cars) if packet.game_cars[i].team == self.team and i != self.index]
        self.foes = [car_object(i,packet) for i in range(packet.num_cars) if packet.game_cars[i].team != self.team]
        self.all_cars = self.friends + self.foes + [self.me]
    def push(self,routine):
        #Shorthand for adding a routine to the stack
        self.stack.append(routine)
    def pop(self):
        #Shorthand for removing a routine from the stack, returns the routine
        return self.stack.pop()
    def line(self,start,end,color=None):
        color = color if color != None else [255,255,255]
        self.renderer.draw_line_3d(start,end,self.renderer.create_color(255,*color))
    def debug_stack(self):
        #Draws the stack on the screen
        white = self.renderer.white()
        for i in range(len(self.stack)-1,-1,-1):
            text = self.stack[i].__class__.__name__
            self.renderer.draw_string_2d(10,50+(50*(len(self.stack)-i)),3,3,text,white)  
    def clear(self):
        #Shorthand for clearing the stack of all routines
        self.stack = []
    def preprocess(self,packet):
        #Calling the update functions for all of the objects
        if packet.num_cars != len(self.friends)+len(self.foes)+1: self.refresh_player_lists(packet)
        for car in self.friends: car.update(packet)
        for car in self.foes: car.update(packet)
        for pad in self.boosts: pad.update(packet)
        self.ball.update(packet)
        self.me.update(packet)
        self.game.update(packet)
        self.time = packet.game_info.seconds_elapsed
        #When a new kickoff begins we empty the stack
        if self.kickoff_flag == False and packet.game_info.is_round_active and packet.game_info.is_kickoff_pause:
            self.stack = []
        #Tells us when to go for kickoff
        self.kickoff_flag = packet.game_info.is_round_active and packet.game_info.is_kickoff_pause

        # Lastly, analyze the game state
        self.analysis.update(self)
    def get_output(self,packet):
        #Reset controller
        self.controller.__init__()
        #Get ready, then preprocess
        if not self.ready:
            self.get_ready(packet)
        self.preprocess(packet)
        
        self.renderer.begin_rendering()
        # run the routine on the end of the stack
        if len(self.stack) > 0:
            self.stack[-1].run(self)
        #Run our strategy code
        self.run()
        self.renderer.end_rendering()
        #send our updated controller back to rlbot
        return self.controller
    def run(self):
        #override this with your strategy code
        pass

class car_object:
    #The carObject, and kin, convert the gametickpacket in something a little friendlier to use,
    #and are updated by GoslingAgent as the game runs
    def __init__(self, index, packet = None):
        self.location = Vector3(0,0,0)
        self.orientation = Matrix3(0,0,0)
        self.velocity = Vector3(0,0,0)
        self.angular_velocity = [0,0,0]
        self.demolished = False
        self.airborne = False
        self.supersonic = False
        self.jumped = False
        self.doublejumped = False
        self.team = 0
        self.boost= 0
        self.index = index
        if packet != None:
            self.team = packet.game_cars[self.index].team
            self.update(packet)
        self.possession = 0
        self.objective = Objective.GO_FOR_IT
        self.last_objective = Objective.GO_FOR_IT
    def local(self,value):
        #Shorthand for self.matrix.dot(value)
        return self.orientation.dot(value)
    def update(self, packet):
        car = packet.game_cars[self.index]
        self.location.data = [car.physics.location.x, car.physics.location.y, car.physics.location.z]
        self.velocity.data = [car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z]
        self.orientation = Matrix3(car.physics.rotation.pitch, car.physics.rotation.yaw, car.physics.rotation.roll)
        self.angular_velocity = self.orientation.dot([car.physics.angular_velocity.x, car.physics.angular_velocity.y, car.physics.angular_velocity.z]).data
        self.demolished = car.is_demolished
        self.airborne = not car.has_wheel_contact
        self.supersonic = car.is_super_sonic
        self.jumped = car.jumped
        self.doublejumped = car.double_jumped
        self.boost = car.boost

class ball_object:
    def __init__(self):
        self.location = Vector3(0,0,0)
        self.velocity = Vector3(0,0,0)
        self.latest_touched_time = 0
        self.latest_touched_team = 0
    def update(self,packet):
        ball = packet.game_ball
        self.location.data = [ball.physics.location.x, ball.physics.location.y, ball.physics.location.z]
        self.velocity.data = [ball.physics.velocity.x, ball.physics.velocity.y, ball.physics.velocity.z]
        self.latest_touched_time = ball.latest_touch.time_seconds
        self.latest_touched_team = ball.latest_touch.team

class boost_object:
    def __init__(self,index,location,large):
        self.index = index
        self.location = Vector3(location.x,location.y,location.z)
        self.active = True
        self.large = large
    def update(self,packet):
        self.active = packet.game_boosts[self.index].is_active

class goal_object:
    #This is a simple object that creates/holds goalpost locations for a given team (for soccer on standard maps only)
    def __init__(self,team):
        team = 1 if team == 1 else -1
        self.location = Vector3(0, team * 5100, 320) #center of goal line
        #Posts are closer to x=750, but this allows the bot to be a little more accurate
        self.left_post = Vector3(team * 850, team * 5100, 320)
        self.right_post = Vector3(-team * 850, team * 5100, 320)

class game_object:
    #This object holds information about the current match
    def __init__(self):
        self.time = 0
        self.time_remaining = 0
        self.overtime = False
        self.round_active = False
        self.kickoff = False
        self.match_ended = False
    def update(self,packet):
        game = packet.game_info
        self.time = game.seconds_elapsed
        self.time_remaining = game.game_time_remaining
        self.overtime = game.is_overtime
        self.round_active = game.is_round_active
        self.kickoff = game.is_kickoff_pause
        self.match_ended = game.is_match_ended
