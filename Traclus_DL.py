from Trajectory import *
from ClusterQ import *
import sys
import datetime
from collections import defaultdict
from numpy import arange
from itertools import count
import math
"""This is a collection of methods to read in a set of 2 dimensional desire lines trajectories, and create segmented Trajectory data structures,
run our adapted angle-based DBScan using each segment as a "seed", putting those that respect the minimum sum of weight (density)
requirement in a priority queue. Clusters are then popped from the queue, the average X and Y of their starts and ends taken, and these output to a file
for visualization in the QVis program. """


#data structures to avoid having to recalculate distances between segments and lines
segment_to_line_dist =  defaultdict(lambda : defaultdict(float))
segment_to_line_closest_seg =  defaultdict(lambda : defaultdict(Trajectory.TrajectorySegment))


def round_to(n, precision):
    correction = precision/2.0 if n >= 0 else -precision/2.0
    return int(n/precision+correction)*precision






def point_segment_distance(px, py, x1, y1, x2, y2):
    """ returns the distance from a point in 2-D (px,py) to a line segment
    going from (x1, y1) to (x12, y12), and also returns the x and y coordinates of the closest point in the line segment to (px,py)
    
    This function is adapted from a stackoverflow.com answer provided by user "Alex Martelli"
    at http://stackoverflow.com/questions/2824478/shortest-distance-between-two-line-segments (last accessed November 6, 2014)
    and is under the Creative Commons License http://creativecommons.org/licenses/by-sa/3.0/
    """
    #    print("called with ", px, py, x1, y1, x2, y2)
    dx = x2 - x1
    dy = y2 - y1
    if dx == dy == 0:  # the segment's just a point
        return math.hypot(px - x1, py - y1)
    
        # Calculate the t that minimizes the distance.
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
# See if this represents one of the segment's
        # end points or a point in the middle.
    near_x = 0
    near_y = 0
    
    if t < 0:
        dx = px - x1
        dy = py - y1
        near_x = x1
        near_y = y1
    elif t > 1:
        dx = px - x2
        dy = py - y2
        near_x = x2
        near_y = y2
    else:
        near_x = x1 + t * dx
        near_y = y1 + t * dy
        dx = px - near_x
        dy = py - near_y
    #if math.hypot(dx,dy) < 101:
    #   print "came up with ", math.hypot(dx,dy), near_x, near_y
    return (math.hypot(dx, dy), near_x, near_y)
    
    





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
                segment_to_line_dist[seg1.id][line2.name], closest_x, closest_y =  point_segment_distance((seg1.startx+seg1.endx)/2, (seg1.starty+seg1.endy)/2, line2.startx, line2.starty, line2.endx, line2.endy)
                if segment_to_line_dist[seg1.id][line2.name] > max_dist:
                    segment_to_line_closest_seg[seg1.id][line2.name] = max_dist + 1;
                else:
                    segment_to_line_closest_seg[seg1.id][line2.name] = line2.get_segment_at(closest_x, closest_y)
                    
            if segment_to_line_dist[seg1.id][line2.name] <= max_dist:
                #Respects both angle and distance limits! add to list of reachable segments and increment weight
                reachable_segs.append(segment_to_line_closest_seg[seg1.id][line2.name])
                sumweight = sumweight + line2.weight

    return sumweight, reachable_segs


def DBScan(seg1, traj_angles,  max_dist, min_weight, max_angle, segment_to_line_dist, segment_to_line_closest_seg):
    """implementation of DBScan with an angle twist. Find segments reachable from seg1 that respect both angle and distance criteria. Then expands cluster as done in 
    classic DBScan, but angles are not allowed to expand, i.e. all final members of the cluster have an angle less than max_angle with the original seg1"""

    reachable_segs = set() #keep track of those reachable from set1
    sumweight, reachable_segs = reachable(seg1, seg1.parent.angle, traj_angles, max_dist, max_angle, segment_to_line_dist, segment_to_line_closest_seg); #add those reachable based on the maximum angle and maximum distance (epsilon)

    if sumweight < min_weight:
        return (-1, [])
    else:
        return expand_cluster(seg1, traj_angles, reachable_segs,  max_dist, min_weight, max_angle,  segment_to_line_dist, segment_to_line_closest_seg)
        

def expand_cluster(seg1, traj_angles, reachable_segs, max_dist, min_weight, max_angle, segment_to_line_dist, segment_to_line_closest_seg):
    """ Expansion of cluster from seg1 as in classic DBScan but angles are not allowed to expand, i.e. all final members of the cluster have an angle less than max_angle with the original seg1"""
    corridor_assignment = set()
    represented_lines = set() # for a given line, only one representative segment per cluster/corridor
    represented_lines.add(seg1.parent)
    expanded_sum_weight = seg1.parent.weight
    corridor_assignment.add(seg1) #this will definitely be in the corridor, and does not need to be expanded as we have found everything reachable from seg1
    while len(reachable_segs) > 0:
        new_candidates = []  #this is the list of segments that we continue to expand
        for seg2 in reachable_segs: 
            
            if seg2 not in corridor_assignment and seg2.parent not in represented_lines:
                represented_lines.add(seg2.parent)
                corridor_assignment.add(seg2)
                expanded_sum_weight += seg2.parent.weight
                
                seg2_sum_weight, new_reachable = reachable(seg2, seg1.parent.angle, traj_angles, max_dist, max_angle, segment_to_line_dist, segment_to_line_closest_seg); #add those reachable based on the maximum angle and maximum distance (epsilon). Note that the second argument is not a typo as the angles are kept close to those of the original "seed" segment (seg1)
                if seg2_sum_weight >= min_weight:
                    for seg3 in new_reachable:
                        if seg3 not in reachable_segs and seg3.parent not in represented_lines:
                            new_candidates.append(seg3)
  
        reachable_segs = new_candidates 

    return (expanded_sum_weight, corridor_assignment)



        



def print_weighted_averages(cluster_segments, corr_number, oh):
    """File output method for printing weighted average of start and ends for the segments assigned to that cluster. File format is designed for visualization with QVis"""
    weightsum = 0.
    x1sum = 0.
    y1sum = 0.
    x2sum = 0.
    y2sum = 0.
    for segment in cluster_segments:
        weightsum += segment.parent.weight
        x1sum += segment.startx * segment.parent.weight
        x2sum += segment.endx * segment.parent.weight
        y1sum += segment.starty * segment.parent.weight
        y2sum += segment.endy * segment.parent.weight
    


    oh.write(str(corr_number) + "\t"+  str(weightsum) + "\tLINESTRING(" + str(x1sum/weightsum) + " "+ str(y1sum/weightsum) + ", " + str(x2sum/weightsum) + " " + str(y2sum/weightsum) + ")\n")


def get_traj_by_name(trajectories, name):
    """Search for particular trajectory name, used mostly for testing purposes"""
    print trajectories
    for traj in trajectories:
        if traj.name == name:
            return traj


def read_file(infile, segment_size, traj_angles, trajectories):
    """File input, one row per desire line with columns corresponding to line name, line weight, start x, start y, end x and end y, with comment lines (not to be included as desire lines
    starting with #"""
    fh = open (infile, 'r') 
    for line in fh:
        if line.startswith("#"):
            continue
        linelist = line.split();
        traj = Trajectory(name=linelist[0], weight = float(linelist[1]), startx=float(linelist[2]), starty=float(linelist[3]), endx=float(linelist[4]), endy=float(linelist[5]))
        traj.make_segments(segment_size)
        rounded_angle = round_to(traj.angle, 0.5);
        traj_angles[rounded_angle].append(traj) #add the trajectory to a list in the dictionary of angles
        trajectories.append(traj)



def build_DB_queue(trajectories, traj_angles, max_dist, min_density, max_angle, segment_to_line_dist, segment_to_line_closest_seg):
    """Create empty ClusterQ, call DBScan with each segment in the set of all desire lines. Add those to the queue that respect minimum weight, return the ClusterQ of all
    segments after DBScan run for all"""
    Q = ClusterQ(min_density)
    for line in trajectories:
        for segment in line.segments:
            sumweight, segments  = DBScan(segment, traj_angles, max_dist, min_density, max_angle, segment_to_line_dist, segment_to_line_closest_seg)
            if sumweight >= min_density:
                Q.add_cluster(segment, segments, int(sumweight*100))
    return Q

if __name__ == '__main__':

    infile = sys.argv[1]
    max_dist = float(sys.argv[2])
    min_density = float(sys.argv[3])
    max_angle = float(sys.argv[4])
    segment_size = float(sys.argv[5])
    
    
# For each line, get candidate lines from angle dictionary, find within distance
    traj_angles = defaultdict(list) #look up angles fast, each angle (in degrees) will have a list of Trajectory objects
    trajectories = [] # list of trajectories, keep it? 
    
    read_file(infile, segment_size, traj_angles, trajectories)
    
    segment_list_oh = open(infile + "." + str(max_dist) + "." + str(min_density)  + "." + str(max_angle) + "." + str(segment_size) + ".segmentlist.txt", "w")
    corridor_list_oh = open (infile + "." + str(max_dist) + "."  + str(min_density) + "." + str(max_angle) + "." + str(segment_size)  + ".corridorlist.txt", "w")
    corridor_list_oh.write("name\tweight\tcoordinates\n");
    segment_list_oh.write("line_id\tweight\tangle\tcorridor_id\tcoordinates\n");

    
    build_DB_queue(trajectories, traj_angles, max_dist, min_density, max_angle, segment_to_line_dist, segment_to_line_closest_seg)

        

    

    #To do, move segment file output to a separate function
    corridor = 0
    assigned = set()
    while True:
        try:
            cluster_segments = pop_cluster()
            print_weighted_averages(cluster_segments, corridor, corridor_list_oh)


            for segment in cluster_segments:
                segment_list_oh.write(segment.parent.name + "\t" + str(segment.parent.weight) + "\t" + str(segment.parent.angle) + "\t"  + str(corridor) + "\tLINESTRING(" + str(segment.startx) + " " + str(segment.starty) + ", " + str(segment.endx) + " " + str(segment.endy) + ")\n")
                assigned.add(str(segment))
            corridor += 1
        
        except KeyError:
            break


    for line in trajectories:
        for segment in line.segments:
            if str(segment) not in assigned:
                segment_list_oh.write(segment.parent.name + "\t" + str(segment.parent.weight) + "\t" + str(segment.parent.angle) + "\t"  + str(-1) + "\tLINESTRING(" + str(segment.startx) + " " + str(segment.starty) + ", " + str(segment.endx) + " " + str(segment.endy) + ")\n")




    
    corridor_list_oh.close()

    segment_list_oh.close()
