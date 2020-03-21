import math

import rlbot.utils.structures.game_data_struct as game_data_struct


class Matrix3:
    #The Matrix3's sole purpose is to convert roll, pitch, and yaw data from the gametickpaket into an orientation matrix
    #An orientation matrix contains 3 Vector3's
    #Matrix3[0] is the "forward" direction of a given car
    #Matrix3[1] is the "left" direction of a given car
    #Matrix3[2] is the "up" direction of a given car
    #If you have a distance between the car and some object, ie ball.location - car.location,
    #you can convert that to local coordinates by dotting it with this matrix
    #ie: local_ball_location = Matrix3.dot(ball.location - car.location)
    def __init__(self,pitch,yaw,roll):
        CP = math.cos(pitch)
        SP = math.sin(pitch)
        CY = math.cos(yaw)
        SY = math.sin(yaw)
        CR = math.cos(roll)
        SR = math.sin(roll)
        #List of 3 vectors, each descriping the direction of an axis: Forward, Left, and Up
        self.data = [
            Vector3(CP*CY, CP*SY, SP),
            Vector3(CY*SP*SR-CR*SY,SY*SP*SR+CR*CY, -CP*SR),
            Vector3(-CR*CY*SP-SR*SY, -CR*SY*SP+SR*CY, CP*CR)]
        self.forward, self.left, self.up = self.data
    def __getitem__(self,key):
        return self.data[key]
    def dot(self,vector):
        return Vector3(self.forward.dot(vector),self.left.dot(vector),self.up.dot(vector))

class Vector3:
    #This is the backbone of Gosling Utils. The Vector3 makes it easy to store positions, velocities, etc and perform vector math
    #A Vector3 can be created with:
    # - Anything that has a __getitem__ (lists, tuples, Vector3's, etc)
    # - 3 numbers
    # - A gametickpacket vector
    def __init__(self, *args):
        if hasattr(args[0],"__getitem__"):
            self.data = list(args[0])
        elif isinstance(args[0], game_data_struct.Vector3):
            self.data = [args[0].x, args[0].y, args[0].z]
        elif isinstance(args[0],game_data_struct.Rotator):
            self.data = [args[0].pitch, args[0].yaw, args[0].roll]
        elif len(args) == 3:
            self.data = list(args)
        else:
            raise TypeError("Vector3 unable to accept %s"%(args))
    #Property functions allow you to use `Vector3.x` vs `Vector3[0]`
    @property
    def x(self):
        return self.data[0]
    @x.setter
    def x(self,value):
        self.data[0] = value
    @property
    def y(self):
        return self.data[1]
    @y.setter
    def y(self,value):
        self.data[1] = value
    @property
    def z(self):
        return self.data[2]
    @z.setter
    def z(self,value):
        self.data[2] = value
    def __getitem__(self,key):
        #To access a single value in a Vector3, treat it like a list
        # ie: to get the first (x) value use: Vector3[0]
        #The same works for setting values
        return self.data[key]
    def __setitem__(self,key,value):
        self.data[key] = value
    def __str__(self):
        #Vector3's can be printed to console
        return str(self.data)
    __repr__ = __str__
    def __eq__(self,value):
        #Vector3's can be compared with:
        # - Another Vector3, in which case True will be returned if they have the same values
        # - A list, in which case True will be returned if they have the same values
        # - A single value, in which case True will be returned if the Vector's length matches the value
        if isinstance(value,Vector3):
            return self.data == value.data
        elif isinstance(value,list):
            return self.data == value
        else:
            return self.magnitude() == value
    #Vector3's support most operators (+-*/)
    #If using an operator with another Vector3, each dimension will be independent
    #ie x+x, y+y, z+z
    #If using an operator with only a value, each dimension will be affected by that value
    #ie x+v, y+v, z+v
    def __add__(self,value):
        if isinstance(value,Vector3):
            return Vector3(self[0]+value[0], self[1]+value[1], self[2]+value[2])
        return Vector3(self[0]+value, self[1]+value, self[2]+value)
    __radd__ = __add__
    def __sub__(self,value):
        if isinstance(value,Vector3):
            return Vector3(self[0]-value[0],self[1]-value[1],self[2]-value[2])
        return Vector3(self[0]-value,self[1]-value,self[2]-value)
    __rsub__ = __sub__
    def __neg__(self):
        return Vector3(-self[0],-self[1],-self[2])
    def __mul__(self,value):
        if isinstance(value,Vector3):
            return Vector3(self[0]*value[0], self[1]*value[1], self[2]*value[2])
        return Vector3(self[0]*value, self[1]*value, self[2]*value)
    __rmul__ = __mul__
    def __truediv__(self,value):
        if isinstance(value,Vector3):
            return Vector3(self[0]/value[0], self[1]/value[1], self[2]/value[2])
        return Vector3(self[0]/value, self[1]/value, self[2]/value)
    def __rtruediv__(self,value):
        if isinstance(value,Vector3):
            return Vector3(value[0]/self[0],value[1]/self[1],value[2]/self[2])
        raise TypeError("unsupported rtruediv operands")
    def magnitude(self):
        #Magnitude() returns the length of the vector
        return math.sqrt((self[0]*self[0]) + (self[1] * self[1]) + (self[2]* self[2]))
    def normalize(self,return_magnitude=False):
        #Normalize() returns a Vector3 that shares the same direction but has a length of 1.0
        #Normalize(True) can also be used if you'd like the length of this Vector3 (used for optimization)
        magnitude = self.magnitude()
        if magnitude != 0:
            if return_magnitude:
                return Vector3(self[0]/magnitude, self[1]/magnitude, self[2]/magnitude),magnitude
            return Vector3(self[0]/magnitude, self[1]/magnitude, self[2]/magnitude)
        if return_magnitude:
            return Vector3(0,0,0),0
        return Vector3(0,0,0)
    #Linear algebra functions
    def dot(self,value):
        return self[0]*value[0] + self[1]*value[1] + self[2]*value[2]
    def cross(self,value):
        return Vector3((self[1]*value[2]) - (self[2]*value[1]),(self[2]*value[0]) - (self[0]*value[2]),(self[0]*value[1]) - (self[1]*value[0]))
    def flatten(self):
        #Sets Z (Vector3[2]) to 0
        return Vector3(self[0],self[1],0)
    def dist(self, other):
        return (self - other).magnitude()
    def render(self):
        #Returns a list with the x and y values, to be used with pygame
        return [self[0],self[1]]
    def copy(self):
        #Returns a copy of this Vector3
        return Vector3(self.data[:])
    def angle(self,value):
        #Returns the angle between this Vector3 and another Vector3
        return math.acos(round(self.flatten().normalize().dot(value.flatten().normalize()),4))
    def rotate(self,angle):
        #Rotates this Vector3 by the given angle in radians
        #Note that this is only 2D, in the x and y axis
        return Vector3((math.cos(angle)*self[0]) - (math.sin(angle)*self[1]),(math.sin(angle)*self[0]) + (math.cos(angle)*self[1]),self[2])
    def clamp(self,start,end):
        #Similar to integer clamping, Vector3's clamp() forces the Vector3's direction between a start and end Vector3
        #Such that Start < Vector3 < End in terms of clockwise rotation
        #Note that this is only 2D, in the x and y axis
        s = self.normalize()
        right = s.dot(end.cross((0,0,-1))) < 0
        left = s.dot(start.cross((0,0,-1))) > 0
        if (right and left) if end.dot(start.cross((0,0,-1))) > 0 else (right or left):
            return self
        if start.dot(s) < end.dot(s):
            return end
        return start