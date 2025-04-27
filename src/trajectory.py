import math
from typing import List, Optional

class TrajectorySegment:
    """
    Represents a segment of a trajectory.
    
    A trajectory segment is a straight line between two points, derived from
    a parent trajectory and used for clustering in the Traclus algorithm.
    """

    def __init__(self, parent_trajectory: "Trajectory", startx: float, starty: float, 
                 end_x: float, end_y: float, weight: float = 1.0, corridor: int = -1):
        """
        Initialize a trajectory segment.
        
        Args:
            parent_trajectory: The parent trajectory this segment belongs to
            startx: X-coordinate of start point
            starty: Y-coordinate of start point
            end_x: X-coordinate of end point
            end_y: Y-coordinate of end point
            weight: Weight of the segment (inherited from parent)
            corridor: Corridor ID this segment belongs to (-1 means unassigned)
        """
        self.parent_trajectory: Trajectory = parent_trajectory
        self.start_x: float = float(startx)
        self.start_y: float = float(starty)
        self.end_x: float = float(end_x)
        self.end_y: float = float(end_y)
        self.weight: float = float(weight)
        self.id: str = f"{parent_trajectory.name}:{startx}:{starty}"
        self.corridor: int = corridor
        
    def __str__(self) -> str:
        return f"TrajectorySegment(id={self.id}, start=({self.start_x}, {self.start_y}), end=({self.end_x}, {self.end_y}))"

    def __repr__(self) -> str:
        return f"TrajectorySegment(parent='{self.parent_trajectory.name}', start_x={self.start_x}, start_y={self.start_y}, end_x={self.end_x}, end_y={self.end_y})"

    def get_length(self) -> float:
        """
        Calculate the length of this segment.
        
        Returns:
            The Euclidean distance between start and end points
        """
        return math.hypot(self.end_y - self.start_y, self.end_x - self.start_x)


class Trajectory:
    """
    Data structure for storing trajectories (i.e., 2-dimensional desire lines).
    
    Information about the segment's angle and length is calculated by the constructor,
    and the trajectory can be segmented to give units that are used during DBScan execution.
    """

    def __init__(self, name: str = "", weight: float = 1.0, start_x: float = 0.0, 
                 start_y: float = 0.0, end_x: float = 1.0, end_y: float = 1.0):
        """
        Initialize a trajectory.
        
        Args:
            name: Identifier for the trajectory
            weight: Weight/importance of the trajectory
            start_x: X-coordinate of start point
            start_y: Y-coordinate of start point
            end_x: X-coordinate of end point
            end_y: Y-coordinate of end point
        """
        self.name: str = str(name)
        self.weight: float = float(weight)
        
        # Validate weight
        if self.weight <= 0:
            raise ValueError("Trajectory weight must be positive")
            
        self.start_x: float = float(start_x)
        self.start_y: float = float(start_y)
        self.end_x: float = float(end_x)
        self.end_y: float = float(end_y)
        
        # Calculate trajectory properties
        self.angle: float = math.atan2(end_y - start_y, end_x - start_x) * 180 / math.pi
        self.length: float = math.hypot(end_y - start_y, end_x - start_x)
        
        # Validate length
        if self.length <= 0:
            raise ValueError("Trajectory must have non-zero length")
            
        self.slope: float = float('inf') if end_x - start_x == 0 else (end_y - start_y) / (end_x - start_x)
        self.segments: List[TrajectorySegment] = []  # Initialize as an empty list
        self.xstep: float = 0.0  # Initialize with default value
        self.ystep: float = 0.0  # Initialize with default value

    def make_segments(self, segment_length: float = 100.0) -> None:
        """
        Segment the trajectory into smaller pieces of approximately equal length.
        
        Args:
            segment_length: Target length for each segment
        
        Raises:
            ValueError: If segment_length is not positive
        """
        if segment_length <= 0:
            raise ValueError("Segment length must be positive")
            
        self.segments = []
        angle_radians: float = math.radians(self.angle)
        self.xstep: float = segment_length * math.cos(angle_radians)
        self.ystep: float = segment_length * math.sin(angle_radians)
        
        # Calculate number of segments, adding small epsilon to avoid floating point precision issues
        nsegs: int = max(1, math.ceil(self.length / segment_length + 1e-5))
        seg_start_x: float = self.start_x
        seg_start_y: float = self.start_y

        for i in range(nsegs):
            # Calculate coordinates for the start and end points of the segment
            segment_start_x: float = seg_start_x + i * self.xstep
            segment_start_y: float = seg_start_y + i * self.ystep
            segment_end_x: float = seg_start_x + (i + 1) * self.xstep
            segment_end_y: float = seg_start_y + (i + 1) * self.ystep
            
            # For the last segment, ensure it doesn't extend past the trajectory end point
            if i == nsegs - 1:
                segment_end_x = self.end_x
                segment_end_y = self.end_y
            
            # Create a TrajectorySegment instance and append it to the list of segments
            self.segments.append(TrajectorySegment(self, segment_start_x, segment_start_y, 
                                                 segment_end_x, segment_end_y, self.weight))

  
    def get_segment_at(self, point_x: float, point_y: float) -> Optional[TrajectorySegment]:
        """
        Get the segment that contains the given point.
        
        Args:
            point_x: X-coordinate of the point
            point_y: Y-coordinate of the point
            
        Returns:
            The segment containing the point, or None if no such segment exists
        """
        # Ensure segments are generated
        if not self.segments:
            self.make_segments()

        # Determine whether x or y step is dominant to avoid division by near-zero
        is_x_dominant: bool = abs(self.xstep) > abs(self.ystep)

        # Calculate segment index based on dominant step
        if is_x_dominant and self.xstep != 0:
            segment_index: int = int((point_x - self.start_x) / self.xstep)
        elif self.ystep != 0:
            segment_index: int = int((point_y - self.start_y) / self.ystep)
        else:
            # Something's wrong - steps shouldn't be zero if segments exist
            return None

        # Return the segment at the calculated index
        if 0 <= segment_index < len(self.segments):
            return self.segments[segment_index]
        return None
