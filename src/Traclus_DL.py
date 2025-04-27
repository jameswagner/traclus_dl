from typing import List, Sequence, Tuple, Set, DefaultDict, Optional, Dict
from .trajectory import Trajectory, TrajectorySegment
from .traclus_priority_queue import TraclusPriorityQueue
from collections import defaultdict
import math
import argparse
import sys
import os
from .file_io import read_file, write_segment_output

"""
Traclus_DL: Trajectory Clustering for Desire Lines

This program implements a modified version of the Traclus algorithm for clustering
2-dimensional desire lines trajectories. It:
1. Reads trajectories and creates segmented Trajectory data structures
2. Runs an adapted angle-based DBScan using each segment as a "seed"
3. Adds clusters that meet minimum weight/density requirements to a priority queue
4. Extracts corridors from the queue in order of priority
5. Outputs results for visualization in QGIS
"""

# Data structures to avoid recalculating distances between segments and lines
segment_to_line_dist: DefaultDict[str, DefaultDict[str, float]] = defaultdict(lambda: defaultdict(float))
segment_to_line_closest_seg: DefaultDict[str, DefaultDict[str, TrajectorySegment]] = defaultdict(lambda: defaultdict(TrajectorySegment))

def point_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float]:
    """
    Calculate the distance from a point to a line segment and the closest point on the segment.
    
    Args:
        px, py: Coordinates of the point
        x1, y1: Coordinates of the first endpoint of the segment
        x2, y2: Coordinates of the second endpoint of the segment
        
    Returns:
        A tuple containing:
            - distance: The shortest distance from the point to the segment
            - near_x, near_y: Coordinates of the closest point on the segment
    
    This function is adapted from a stackoverflow.com answer provided by user "Alex Martelli"
    at http://stackoverflow.com/questions/2824478/shortest-distance-between-two-line-segments 
    (last accessed November 6, 2014) and is under the Creative Commons License 
    http://creativecommons.org/licenses/by-sa/3.0/
    """
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == dy == 0:  # If the segment's just a point
        return math.hypot(px - x1, py - y1), x1, y1

    # Calculate projection parameter
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
    # Find nearest point on segment
    if t < 0:
        near_x, near_y = x1, y1
    elif t > 1:
        near_x, near_y = x2, y2
    else:
        near_x = x1 + t * dx
        near_y = y1 + t * dy

    # Calculate distance
    dx = px - near_x
    dy = py - near_y

    return math.hypot(dx, dy), near_x, near_y
    
def reachable(seg1: TrajectorySegment, seg_angle: float, 
             traj_angles: Dict[float, List[Trajectory]], 
             max_dist: float, max_angle: float,
             segment_to_line_dist: DefaultDict[str, DefaultDict[str, float]],
             segment_to_line_closest_seg: DefaultDict[str, DefaultDict[str, TrajectorySegment]]
             ) -> Tuple[float, List[TrajectorySegment]]:
    """
    Find all segments reachable from a given segment within angle and distance constraints.
    
    Args:
        seg1: The seed segment
        seg_angle: The angle of the segment (in degrees)
        traj_angles: Dictionary mapping angles to trajectories
        max_dist: Maximum distance threshold
        max_angle: Maximum angle threshold (in degrees)
        segment_to_line_dist: Cache of segment-to-line distance calculations
        segment_to_line_closest_seg: Cache of closest segments
        
    Returns:
        A tuple containing:
            - sumweight: Total weight of reachable segments
            - reachable_segs: List of reachable segments
    """
    reachable_segs = []
    sumweight = 0.0
    
    # Calculate segment midpoint once
    seg_mid_x = (seg1.start_x + seg1.end_x) / 2
    seg_mid_y = (seg1.start_y + seg1.end_y) / 2
    
    for angle in traj_angles:
        # Only consider trajectories with angles within max_angle of seg_angle
        if abs(angle - seg_angle) > max_angle:
            continue

        for line2 in traj_angles[angle]:
            # Calculate distance if not already in cache
            if line2.name not in segment_to_line_dist[seg1.id]:
                dist, closest_x, closest_y = point_segment_distance(
                    seg_mid_x, seg_mid_y, 
                    line2.start_x, line2.start_y, 
                    line2.end_x, line2.end_y
                )
                
                segment_to_line_dist[seg1.id][line2.name] = dist
                
                if dist > max_dist:
                    # Set above max_dist so we don't consider it again
                    segment_to_line_dist[seg1.id][line2.name] = max_dist + 1
                else:
                    # Find the segment containing the closest point
                    closest_seg = line2.get_segment_at(closest_x, closest_y)
                    if closest_seg:
                        segment_to_line_closest_seg[seg1.id][line2.name] = closest_seg
                    else:
                        # If no segment found, skip this line
                        segment_to_line_dist[seg1.id][line2.name] = max_dist + 1
                        continue
            
            # If within distance threshold, add to reachable segments
            if segment_to_line_dist[seg1.id][line2.name] <= max_dist:
                # Respects both angle and distance limits
                closest_seg = segment_to_line_closest_seg[seg1.id][line2.name]
                reachable_segs.append(closest_seg)
                sumweight += line2.weight

    return sumweight, reachable_segs


def db_scan(seg1: TrajectorySegment, 
           traj_angles: Dict[float, List[Trajectory]],
           max_dist: float, min_weight: float, max_angle: float,
           segment_to_line_dist: DefaultDict[str, DefaultDict[str, float]],
           segment_to_line_closest_seg: DefaultDict[str, DefaultDict[str, TrajectorySegment]]
           ) -> Tuple[float, Set[TrajectorySegment]]:
    """
    Implementation of DBScan with an angle constraint.
    
    Find segments reachable from seg1 that respect both angle and distance criteria.
    Then expands cluster as in classic DBScan, but angles are not allowed to expand
    (all final members of the cluster have an angle less than max_angle with seg1).
    
    Args:
        seg1: The seed segment
        traj_angles: Dictionary mapping angles to trajectories
        max_dist: Maximum distance threshold
        min_weight: Minimum weight/density threshold
        max_angle: Maximum angle threshold (in degrees)
        segment_to_line_dist: Cache of segment-to-line distance calculations
        segment_to_line_closest_seg: Cache of closest segments
        
    Returns:
        A tuple containing:
            - Total weight of the cluster (or -1 if below threshold)
            - Set of segments in the cluster (or empty if below threshold)
    """
    # Find segments reachable from the seed
    sumweight, reachable_segs = reachable(
        seg1, seg1.parent_trajectory.angle, traj_angles, 
        max_dist, max_angle, segment_to_line_dist, segment_to_line_closest_seg
    )

    # If below density threshold, return empty cluster
    if sumweight < min_weight:
        return (-1, set())
    else:
        # Otherwise expand the cluster
        return expand_cluster(
            seg1, traj_angles, reachable_segs, 
            max_dist, min_weight, max_angle, 
            segment_to_line_dist, segment_to_line_closest_seg
        )
        

def expand_cluster(seg1: TrajectorySegment, 
                  traj_angles: Dict[float, List[Trajectory]],
                  reachable_segs: List[TrajectorySegment], 
                  max_dist: float, min_weight: float, max_angle: float,
                  segment_to_line_dist: DefaultDict[str, DefaultDict[str, float]],
                  segment_to_line_closest_seg: DefaultDict[str, DefaultDict[str, TrajectorySegment]]
                  ) -> Tuple[float, Set[TrajectorySegment]]:
    """
    Expand a cluster from a seed segment following DBScan principles.
    
    All segments in the final cluster have angles within max_angle of the original seed segment.
    
    Args:
        seg1: The seed segment
        traj_angles: Dictionary mapping angles to trajectories
        reachable_segs: Initial list of reachable segments
        max_dist: Maximum distance threshold
        min_weight: Minimum weight/density threshold
        max_angle: Maximum angle threshold (in degrees)
        segment_to_line_dist: Cache of segment-to-line distance calculations
        segment_to_line_closest_seg: Cache of closest segments
        
    Returns:
        A tuple containing:
            - Total weight of the expanded cluster
            - Set of segments in the expanded cluster
    """
    corridor_assignment = set()
    represented_lines = set()  # For a given line, only one representative segment per cluster
    
    # Add seed segment to cluster
    represented_lines.add(seg1.parent_trajectory)
    expanded_sum_weight = seg1.parent_trajectory.weight
    corridor_assignment.add(seg1)
    
    # Iteratively expand cluster
    while reachable_segs:
        new_candidates = []  # List of segments to consider in next iteration
        
        for seg2 in reachable_segs:
            # Only add segments from trajectories not already represented
            if seg2 not in corridor_assignment and seg2.parent_trajectory not in represented_lines:
                represented_lines.add(seg2.parent_trajectory)
                corridor_assignment.add(seg2)
                expanded_sum_weight += seg2.parent_trajectory.weight
                
                # Find segments reachable from this new member
                # Note: Using seg1's angle to maintain angle constraint with seed
                seg2_sum_weight, new_reachable = reachable(
                    seg2, seg1.parent_trajectory.angle, traj_angles,
                    max_dist, max_angle, segment_to_line_dist, segment_to_line_closest_seg
                )
                
                # If this segment meets density threshold, consider its neighbors
                if seg2_sum_weight >= min_weight:
                    for seg3 in new_reachable:
                        if seg3 not in reachable_segs and seg3.parent_trajectory not in represented_lines:
                            new_candidates.append(seg3)
  
        reachable_segs = new_candidates 

    return (expanded_sum_weight, corridor_assignment)

def get_traj_by_name(trajectories: List[Trajectory], name: str) -> Optional[Trajectory]:
    """
    Search for a trajectory by name.
    
    Args:
        trajectories: List of trajectories to search
        name: Name to search for
        
    Returns:
        The matching trajectory or None if not found
    """
    for traj in trajectories:
        if traj.name == name:
            return traj
    return None


def build_queue(trajectories: List[Trajectory], 
               traj_angles: Dict[float, List[Trajectory]],
               max_dist: float, min_density: float, max_angle: float,
               segment_to_line_dist: DefaultDict[str, DefaultDict[str, float]],
               segment_to_line_closest_seg: DefaultDict[str, DefaultDict[str, TrajectorySegment]]
               ) -> TraclusPriorityQueue:
    """
    Build a priority queue of clusters by running DBScan on each segment.
    
    Args:
        trajectories: List of all trajectories
        traj_angles: Dictionary mapping angles to trajectories
        max_dist: Maximum distance threshold
        min_density: Minimum density/weight threshold
        max_angle: Maximum angle threshold (in degrees)
        segment_to_line_dist: Cache of segment-to-line distance calculations
        segment_to_line_closest_seg: Cache of closest segments
        
    Returns:
        Priority queue containing all clusters that meet the density threshold
    """
    pq = TraclusPriorityQueue(min_density)
    
    total_segments = sum(len(line.segments) for line in trajectories)
    processed = 0
    
    print(f"Building clusters from {total_segments} segments...")
    
    for line in trajectories:
        for segment in line.segments:
            sumweight, segments = db_scan(
                segment, traj_angles, max_dist, min_density, max_angle,
                segment_to_line_dist, segment_to_line_closest_seg
            )
            
            if sumweight >= min_density:
                pq.add_cluster(segment, list(segments), sumweight)
                
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed}/{total_segments} segments")
    
    print(f"Added {len(pq.pq)} clusters to priority queue")
    return pq


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Namespace containing parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Traclus_DL: Trajectory Clustering for Desire Lines",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-i", "--infile", help="Input file with trajectories", required=True)
    parser.add_argument("-d", "--max_dist", type=float, help="Maximum distance threshold", required=True)
    parser.add_argument("-n", "--min_density", type=float, help="Minimum density/weight threshold", required=True)
    parser.add_argument("-a", "--max_angle", type=float, help="Maximum angle threshold (degrees)", required=True)
    parser.add_argument("-s", "--segment_size", type=float, help="Size of trajectory segments", required=True)
    
    return parser.parse_args()


def pop_corridors_from_queue(pq: TraclusPriorityQueue) -> List[List[TrajectorySegment]]:
    """
    Extract corridors from the priority queue in order of priority.
    
    Args:
        pq: Priority queue of clusters
        
    Returns:
        List of corridors, each containing a list of segments
    """
    corridor_id = 0
    corridors: List[List[TrajectorySegment]] = []
    
    print("Extracting corridors from priority queue...")
    
    while True:
        cluster_segments = pq.pop_cluster()
        if not cluster_segments:
            break
            
        corridors.append(list(cluster_segments))
        
        # Assign corridor ID to each segment
        for segment in cluster_segments:
            segment.corridor = corridor_id
            
        print(f"Extracted corridor {corridor_id} with {len(cluster_segments)} segments")
        corridor_id += 1

    print(f"Total corridors found: {len(corridors)}")
    return corridors


def main() -> int:
    """
    Main function to run the Traclus_DL algorithm.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        args = parse_arguments()

        infile = args.infile
        max_dist = args.max_dist
        min_density = args.min_density
        max_angle = args.max_angle
        segment_size = args.segment_size
        
        # Validate parameters
        if max_dist <= 0:
            raise ValueError("Maximum distance must be positive")
        if min_density <= 0:
            raise ValueError("Minimum density must be positive")
        if segment_size <= 0:
            raise ValueError("Segment size must be positive")
        
        print(f"Reading trajectories from {infile}...")
        trajectories, traj_angles = read_file(infile, segment_size)
        print(f"Read {len(trajectories)} trajectories")
        
        segment_list_out_file = f"{infile}.{max_dist}.{min_density}.{max_angle}.{segment_size}.segmentlist.txt"
        corridor_list_out_file = f"{infile}.{max_dist}.{min_density}.{max_angle}.{segment_size}.corridorlist.txt"
        
        # Build priority queue of clusters
        pq = build_queue(
            trajectories, traj_angles, max_dist, min_density, max_angle,
            segment_to_line_dist, segment_to_line_closest_seg
        )
        
        # Extract corridors from queue
        corridors = pop_corridors_from_queue(pq)
        
        # Write results to output files
        write_segment_output(trajectories, corridors, segment_list_out_file, corridor_list_out_file)
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
