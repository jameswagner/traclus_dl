import math
from numpy import arctan2, hypot, sin, cos, tan
class Trajectory:
    """Data structure for storing tracjectories (i.e. 2 dimensional desire lines. Information about the segments angle and length are calculated by the constructor, and
    trajectory can be segmented to give units that are used during DBScan execution"""

    def __init__(self, name="", weight=1., startx=0., starty=0., endx=1., endy=1.  ):
        self.name = name
        self.weight = weight
        self.startx = startx
        self.starty = starty
        self.endx = endx
        self.endy = endy
        self.angle = arctan2(endy-starty, endx-startx) * 180 / math.pi
        self.length = hypot(endy-starty, endx-startx)
        
        self.slope = 0
        
        if endx - startx == 0:
            self.slope = float('inf')
        else:
            self.slope = (endy - starty) / (endx - startx)
        self.segments = []
        self.xstep = []
        self.ystep = []

    def make_segments(self, segment_length=100., ):
        """segments the trajectory """
        self.segments = []
        self.xstep = segment_length*cos(self.angle * math.pi / 180.0 )
        self.ystep = segment_length*sin(self.angle * math.pi / 180.0)
        nsegs = int(math.ceil(self.length/segment_length + 1e-5 ))
        seg_startx = self.startx
        seg_starty = self.starty
        
        for i in range(0,nsegs):
            self.segments.append(self.TrajectorySegment(self, seg_startx, seg_starty, seg_startx+self.xstep, seg_starty+self.ystep))
            seg_startx += self.xstep
            seg_starty += self.ystep

  
    def get_segment_at(self, pointx, pointy):
        if len(self.segments) < 1:
            self.make_segments()
        if abs(self.xstep) < abs(self.ystep) :
           return self.segments[int((pointy-self.starty)/self.ystep)] 
        return self.segments[int((pointx-self.startx)/self.xstep)]



    class TrajectorySegment:
        """Trajectory Segment"""
        def __init__(self, parent, startx, starty, endx, endy):
            self.parent = parent
            self.startx = startx
            self.starty = starty
            self.endx = endx 
            self.endy = endy
            self.id = parent.name + ":" + str(startx) + ":" +  str(starty)
        def __str__(self):
            return self.id
        def __repr__(self):
            return self.__str__()
