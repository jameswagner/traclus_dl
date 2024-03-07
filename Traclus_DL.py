from typing import List, Sequence
from trajectory import Trajectory, TrajectorySegment
from traclus_priority_queue import TraclusPriorityQueue
from collections import defaultdict
import math
import argparse
from file_io import read_file, write_segment_output

"""This is a collection of methods to read in a set of 2 dimensional desire lines trajectories, and create segmented Trajectory data structures,
run our adapted angle-based DBScan using each segment as a "seed", putting those that respect the minimum sum of weight (density)
requirement in a priority queue. Clusters are then popped from the queue, the average X and Y of their starts and ends taken, and these output to a file
for visualization in the QVis program. """


#data structures to avoid having to recalculate distances between segments and lines
segment_to_line_dist =  defaultdict(lambda : defaultdict(float))
segment_to_line_closest_seg =  defaultdict(lambda : defaultdict(TrajectorySegment))

def point_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> tuple[float, float, float]:
    """ returns the distance from a point in 2-D (px,py) to a line segment
    going from (x1, y1) to (x12, y12), and also returns the x and y coordinates of the closest point in the line segment to (px,py)
    
    This function is adapted from a stackoverflow.com answer provided by user "Alex Martelli"
    at http://stackoverflow.com/questions/2824478/shortest-distance-between-two-line-segments (last accessed November 6, 2014)
    and is under the Creative Commons License http://creativecommons.org/licenses/by-sa/3.0/
    """
    dx = x2 - x1
    dy = y2 - y1
    

    if dx == dy == 0:  # If the segment's just a point
        return math.hypot(px - x1, py - y1), x1, y1

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
    if t < 0:
        near_x, near_y = x1, y1
    elif t > 1:
        near_x, near_y = x2, y2
    else:
        near_x = x1 + t * dx
        near_y = y1 + t * dy

    dx = px - near_x
    dy = py - near_y

    return math.hypot(dx, dy), near_x, near_y
    
def reachable(seg1, seg_angle, traj_angles, max_dist, max_angle, segment_to_line_dist, segment_to_line_closest_seg):
    """For a given segment and other parameters (the maximum angle, maximum distance), find all other segments reachable from that segment"""
    reachable_segs = []
    sumweight = 0.
    for angle in traj_angles:
        #go through the dictionary of angles, only consider those that are less than max_angle from the seg_angle
        if abs(angle - seg_angle) > max_angle:
            continue

        for line2 in traj_angles[angle]:
            #go through the lines for that angle, calculate distance of that line to that segment if not already done, and then check if less than max dist
            if(line2.name not in segment_to_line_dist[seg1.id]): #segment_to_line_dist keeps track of distances already calculated, avoid more than once
                segment_to_line_dist[seg1.id][line2.name], closest_x, closest_y =  point_segment_distance((seg1.start_x+seg1.end_x)/2, (seg1.start_y+seg1.end_y)/2, line2.start_x, line2.start_y, line2.end_x, line2.end_y)
                if segment_to_line_dist[seg1.id][line2.name] > max_dist:
                    segment_to_line_dist[seg1.id][line2.name] = max_dist + 1 #set it above max_dist so we don't consider it again
                else:
                    segment_to_line_closest_seg[seg1.id][line2.name] = line2.get_segment_at(closest_x, closest_y)
                    
            if segment_to_line_dist[seg1.id][line2.name] <= max_dist:
                #Respects both angle and distance limits! add to list of reachable segments and increment weight
                reachable_segs.append(segment_to_line_closest_seg[seg1.id][line2.name])
                sumweight = sumweight + line2.weight

    return sumweight, reachable_segs


def db_scan(seg1, traj_angles,  max_dist, min_weight, max_angle, segment_to_line_dist, segment_to_line_closest_seg):
    """implementation of DBScan with an angle twist. Find segments reachable from seg1 that respect both angle and distance criteria. Then expands cluster as done in 
    classic DBScan, but angles are not allowed to expand, i.e. all final members of the cluster have an angle less than max_angle with the original seg1"""

    sumweight, reachable_segs = reachable(seg1, seg1.parent_trajectory.angle, traj_angles, max_dist, max_angle, segment_to_line_dist, segment_to_line_closest_seg); #add those reachable based on the maximum angle and maximum distance (epsilon)

    if sumweight < min_weight:
        return (-1, [])
    else:
        return expand_cluster(seg1, traj_angles, reachable_segs,  max_dist, min_weight, max_angle,  segment_to_line_dist, segment_to_line_closest_seg)
        

def expand_cluster(seg1, traj_angles, reachable_segs, max_dist, min_weight, max_angle, segment_to_line_dist, segment_to_line_closest_seg):
    """ Expansion of cluster from seg1 as in classic DBScan but angles are not allowed to expand, i.e. all final members of the cluster have an angle less than max_angle with the original seg1"""
    corridor_assignment = set()
    represented_lines = set() # for a given line, only one representative segment per cluster/corridor
    represented_lines.add(seg1.parent_trajectory)
    expanded_sum_weight = seg1.parent_trajectory.weight
    corridor_assignment.add(seg1) #this will definitely be in the corridor, and does not need to be expanded as we have found everything reachable from seg1
    while len(reachable_segs) > 0:
        new_candidates = []  #this is the list of segments that we continue to expand
        for seg2 in reachable_segs: 
            
            if seg2 not in corridor_assignment and seg2.parent_trajectory not in represented_lines:
                represented_lines.add(seg2.parent_trajectory)
                corridor_assignment.add(seg2)
                expanded_sum_weight += seg2.parent_trajectory.weight
                
                seg2_sum_weight, new_reachable = reachable(seg2, seg1.parent_trajectory.angle, traj_angles, max_dist, max_angle, segment_to_line_dist, segment_to_line_closest_seg); #add those reachable based on the maximum angle and maximum distance (epsilon). Note that the second argument is not a typo as the angles are kept close to those of the original "seed" segment (seg1)
                if seg2_sum_weight >= min_weight:
                    for seg3 in new_reachable:
                        if seg3 not in reachable_segs and seg3.parent_trajectory not in represented_lines:
                            new_candidates.append(seg3)
  
        reachable_segs = new_candidates 

    return (expanded_sum_weight, corridor_assignment)

def get_traj_by_name(trajectories, name):
    """Search for particular trajectory name, used mostly for testing purposes"""
    for traj in trajectories:
        if traj.name == name:
            return traj


def build_queue(trajectories, traj_angles, max_dist, min_density, max_angle, segment_to_line_dist, segment_to_line_closest_seg):
    """Create empty ClusterQ, call DBScan with each segment in the set of all desire lines. Add those to the queue that respect minimum weight, return the ClusterQ of all
    segments after DBScan run for all"""
    pq = TraclusPriorityQueue(min_density)
    for line in trajectories:
        for segment in line.segments:
            sumweight, segments  = db_scan(segment, traj_angles, max_dist, min_density, max_angle, segment_to_line_dist, segment_to_line_closest_seg)
            if sumweight >= min_density:
                pq.add_cluster(segment, segments, sumweight)
    return pq


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process trajectories and clusters")
    parser.add_argument("-i", "--infile", help="Input file", required=True)
    parser.add_argument("-d", "--max_dist", type=float, help="Maximum distance", required=True)
    parser.add_argument("-n", "--min_density", type=float, help="Minimum density", required=True)
    parser.add_argument("-a", "--max_angle", type=float, help="Maximum angle", required=True)
    parser.add_argument("-s", "--segment_size", type=float, help="Segment size", required=True)
    return parser.parse_args()


def pop_corridors_from_queue(pq: TraclusPriorityQueue) -> List[List[Sequence[TrajectorySegment]]]:
    corridor = 0
    corridors: List[Sequence[TrajectorySegment]] = []

    while cluster_segments := pq.pop_cluster():
        corridors.append(cluster_segments)
        for segment in cluster_segments:
            segment.corridor = corridor
        corridor += 1

    return corridors


if __name__ == '__main__':

    args = parse_arguments()

    infile = args.infile
    max_dist = args.max_dist
    min_density = args.min_density
    max_angle = args.max_angle
    segment_size = args.segment_size
    
    trajectories, traj_angles = read_file(infile, segment_size)
    
    segment_list_out_file = f"{infile}.{max_dist}.{min_density}.{max_angle}.{segment_size}.segmentlist.txt"
    corridor_list_out_file = f"{infile}.{max_dist}.{min_density}.{max_angle}.{segment_size}.corridorlist.txt"
    
    pq = build_queue(trajectories, traj_angles, max_dist, min_density, max_angle, segment_to_line_dist, segment_to_line_closest_seg)
    corridors = pop_corridors_from_queue(pq)
        
    write_segment_output(trajectories, corridors, segment_list_out_file, corridor_list_out_file)
