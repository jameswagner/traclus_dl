import math
from numpy import arctan2, hypot, sin, cos, tan
class Trajectory:
    """Tracjectory"""
    def __init__(self, name="", weight=1., startx=0., starty=0., endx=1., endy=1.  ):
        self.name = name
        self.weight = weight
        self.startx = startx
        self.starty = starty
        self.endx = endx
        self.endy = endy
        self.endx_rotated = endx
        self.endy_rotated = endy

        self.angle = arctan2(endy-starty, endx-startx) * 180 / math.pi
        self.rotated_angle = self.angle
        self.length = hypot(endy-starty, endx-startx)
        self.corridor = -1
        self.visited = False 
        self.slope = 0
        
        if endx - startx == 0:
            self.slope = float('inf')
        else:
            self.slope = (endy - starty) / (endx - startx)
        print self.angle, self.slope, tan(self.angle/180*math.pi)
        self.rotated_slope = self.slope
        #print self.angle, self.length

    def simple_partition(segment_length=100., ):
        """return list of lines"""
        self.xstarts = arange(self.startx, self.endx, segment_length*sin(self.angle))
        self.ystarts = arange(self.starty, self.endy, segment_length*cos(self.angle))
        self.xmids = arange(self.startx+segment_length*sin(self.angle)/2, self.endy, segment_length*sin(self.angle))
        self.ymids = arange(self.starty+segment_length*cos(self.angle)/2, self.endy, segment_length*cos(self.angle))


    def getY(self, X):
        if X < self.startx or X > self.endx:
            return None
        if self.slope == float('inf'):
            return self.starty
        return (X-self.startx)*self.slope + self.starty

        
    def getY_rotated(self, X):
        if X < self.startx or X > self.endx_rotated:
            return None
        if self.rotated_slope == float('inf'):
            return self.starty
        return (X-self.startx)*self.rotated_slope + self.starty


    def rotate(self,theta=0.):
        theta = float(theta)
        if abs(self.rotated_angle + theta) == 90: #avoid exactly vertical lines
            theta += 0.1
        
        print theta, theta/180*math.pi

        xdiff = self.endx - self.startx
        ydiff = self.endy - self.starty


        newx = xdiff*cos(theta/180*math.pi) - ydiff*sin(theta/180.0*math.pi) + self.startx
        newy = xdiff*sin(theta/180*math.pi) + ydiff*cos(theta/180.0*math.pi) + self.starty
        self.endx_rotated = newx
        self.endy_rotated = newy
        print "called", self.startx, self.starty, self.endx, self.endy, newx, newy
        self.rotated_angle = self.rotated_angle + theta
        
        if newx - self.startx == 0:
            self.rotated_slope = float('inf')
        else:
            self.rotated_slope = (newy - self.starty) / (newx - self.startx)        




X = Trajectory(startx=1, starty=1, endx=2, endy=2)
X.rotate(-45)
print(X.endx_rotated, X.endy_rotated, X.angle, X.rotated_angle, X.rotated_slope, tan(X.rotated_angle*math.pi/180))

        
