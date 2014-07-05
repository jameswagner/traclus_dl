import math
from numpy import arctan2, hypot, sin, cos
class Trajectory:
    """Tracjectory"""
    def __init__(self, name="", weight=1., startx=0., starty=0., endx=1., endy=1.  ):
        self.name = name
        self.weight = weight
        self.startx = startx
        self.starty = starty
        self.endx = endx
        self.endy = endy
        self.angle = arctan2(endy-starty, endx-startx) * 180 / math.pi
        self.length = hypot(endy-starty, endx-startx)
        self.corridor = -1
        self.visited = False 
        self.slope = 0
        if endx - startx == 0:
            self.slope = float('inf')
        else:
            self.slope = (endy - starty) / (endx - startx)
        print self.angle, self.length

    def simple_partition(segment_length=100., ):
        """return list of lines"""
        self.xstarts = arange(self.startx, self.endx, segment_length*sin(self.angle))
        self.ystarts = arange(self.starty, self.endy, segment_length*cos(self.angle))
        self.xmids = arange(self.startx+segment_length*sin(self.angle)/2, self.endy, segment_length*sin(self.angle))
        self.ymids = arange(self.starty+segment_length*cos(self.angle)/2, self.endy, segment_length*cos(self.angle))


    def getY(X):
        if self.slope == float('inf'):
            return self.starty
        return (X-self.startx)*self.slope + self.starty

        



    def rotate(self,theta=0.):
#        xChange = self.length*cos(angle/180*math.pi)
#        yChange = self.length*sin(angle/180*math.pi)

        newx = self.endx*cos(theta/180*math.pi) - self.endy*sin(theta/180.0*math.pi)
        newy = self.endx*sin(theta/180*math.pi) + self.endy*cos(theta/180.0*math.pi)

        print self.startx, self.starty, self.endx, self.endy, newx, newy


traj = Trajectory("", 1, 0, 0, 0, 1)
traj.rotate(-45.0)
        
