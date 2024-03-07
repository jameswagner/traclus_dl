import math
from typing import List, Optional

class TrajectorySegment:
    """Trajectory Segment"""

    def __init__(self, parent_trajectory: "Trajectory", startx: float, starty: float, end_x: float, end_y: float, weight: float = 1.0, corridor: Optional[int] = -1):
        self.parent_trajectory: Trajectory = parent_trajectory
        self.start_x: float = startx
        self.start_y: float = starty
        self.end_x: float = end_x
        self.end_y: float = end_y
        self.weight: float = weight
        self.id: str = f"{parent_trajectory.name}:{startx}:{starty}"
        self.corridor: int = corridor
        
    def __str__(self) -> str:
        return f"TrajectorySegment(id={self.id}, start=({self.start_x}, {self.start_y}), end=({self.end_x}, {self.end_y}))"

    def __repr__(self) -> str:
        return f"TrajectorySegment(parent='{self.parent_trajectory.name}', start_x={self.start_x}, start_y={self.start_y}, end_x={self.end_x}, end_y={self.end_y})"


class Trajectory:
    """Data structure for storing trajectories (i.e., 2-dimensional desire lines).
    Information about the segment's angle and length is calculated by the constructor,
    and the trajectory can be segmented to give units that are used during DBScan execution."""

    def __init__(self, name: str = "", weight: float = 1., start_x: float = 0., start_y: float = 0., end_x: float = 1., end_y: float = 1.):
        self.name: str = name
        self.weight: float = weight
        self.start_x: float = start_x
        self.start_y: float = start_y
        self.end_x: float = end_x
        self.end_y: float = end_y
        self.angle: float = math.atan2(end_y - start_y, end_x - start_x) * 180 / math.pi
        self.length: float = math.hypot(end_y - start_y, end_x - start_x)
        self.slope: float = float('inf') if end_x - start_x == 0 else (end_y - start_y) / (end_x - start_x)
        self.segments: List[TrajectorySegment] = []  # Initialize as an empty list
        self.xstep: float = 0.0  # Initialize with default value
        self.ystep: float = 0.0  # Initialize with default value

    def make_segments(self, segment_length: float = 100.):
        """Segments the trajectory."""
        self.segments: List[TrajectorySegment] = []
        angle_radians: float = math.radians(self.angle)
        self.xstep: float = segment_length * math.cos(angle_radians)
        self.ystep: float = segment_length * math.sin(angle_radians)
        nsegs: int = math.ceil(self.length / segment_length + 1e-5)
        seg_start_x: float = self.start_x
        seg_start_y: float = self.start_y

        for i in range(nsegs):
            # Calculate coordinates for the start and end points of the segment
            segment_start_x: float = seg_start_x + i * self.xstep
            segment_start_y: float = seg_start_y + i * self.ystep
            segment_end_x: float = seg_start_x + (i + 1) * self.xstep
            segment_end_y: float = seg_start_y + (i + 1) * self.ystep
            
            # Create a TrajectorySegment instance and append it to the list of segments
            self.segments.append(TrajectorySegment(self, segment_start_x, segment_start_y, segment_end_x, segment_end_y, self.weight))

  
    def get_segment_at(self, point_x: float, point_y: float) -> Optional[TrajectorySegment]:
        # Ensure segments are generated
        if not self.segments:
            self.make_segments()

        # Determine whether x or y step is dominant
        is_x_dominant: bool = abs(self.xstep) > abs(self.ystep)

        # Calculate segment index based on dominant step
        if is_x_dominant:
            segment_index: int = int((point_x - self.start_x) / self.xstep)
        else:
            segment_index: int = int((point_y - self.start_y) / self.ystep)

        # Return the segment at the calculated index
        return self.segments[segment_index] if 0 <= segment_index < len(self.segments) else None
