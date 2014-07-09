from Trajectory import *
import sys
from collections import defaultdict
from numpy import arange
step_size = 1.0
def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int(n/precision+correction)*precision







def segments_distance(x11, y11, x12, y12, x21, y21, x22, y22):
  """ distance between two segments in the plane:
      one segment is (x11, y11) to (x12, y12)
      the other is   (x21, y21) to (x22, y22)
  """
  if segments_intersect(x11, y11, x12, y12, x21, y21, y22, y22): return 0
  # try each of the 4 vertices w/the other segment
  distances = []
  distances.append(point_segment_distance(x11, y11, x21, y21, x22, y22))
  distances.append(point_segment_distance(x12, y12, x21, y21, x22, y22))
  distances.append(point_segment_distance(x21, y21, x11, y11, x12, y12))
  distances.append(point_segment_distance(x22, y22, x11, y11, x12, y12))

  return min(distances)

def segments_intersect(x11, y11, x12, y12, x21, y21, x22, y22):
  """ whether two segments in the plane intersect:
      one segment is (x11, y11) to (x12, y12)
      the other is   (x21, y21) to (x22, y22)
  """
  dx1 = x12 - x11
  dy1 = y12 - y11
  dx2 = x22 - x21
  dy2 = y22 - y21
  delta = dx2 * dy1 - dy2 * dx1
  if delta == 0: return False  # parallel segments
  s = (dx1 * (y21 - y11) + dy1 * (x11 - x21)) / delta
  t = (dx2 * (y11 - y21) + dy2 * (x21 - x11)) / (-delta)
  return (0 <= s <= 1) and (0 <= t <= 1)

import math
def point_segment_distance(px, py, x1, y1, x2, y2):
  dx = x2 - x1
  dy = y2 - y1
  if dx == dy == 0:  # the segment's just a point
    return math.hypot(px - x1, py - y1)

  # Calculate the t that minimizes the distance.
  t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)

  # See if this represents one of the segment's
  # end points or a point in the middle.
  if t < 0:
    dx = px - x1
    dy = py - y1
  elif t > 1:
    dx = px - x2
    dy = py - y2
  else:
    near_x = x1 + t * dx
    near_y = y1 + t * dy
    dx = px - near_x
    dy = py - near_y

  return math.hypot(dx, dy)
corridors = []
def DBScan(line1, traj_angles, current_corridor):
    if line1.visited == True or line1.corridor >= 0:
        return current_corridor
    reachable = []
    line1.visited = True
    sumweight = 0.0
    for angle in traj_angles:

        if abs(angle - line1.angle) > max_angle:
            continue

        for line2 in traj_angles[angle]:
            
            if segments_distance(line1.startx, line1.starty, line1.endx, line1.endy, line2.startx, line2.starty, line2.endx, line2.endy) <= max_dist:
                reachable.append(line2)
                sumweight = sumweight + line2.weight
                
    #print reachable, sumweight            
    if sumweight < min_density:
        line1.corridor = -1 #did not reach minimum density, assign line1 to noise cluster
        return current_corridor
    else:
        expand_cluster(line1, reachable, current_corridor)
        current_corridor = current_corridor + 1
        return current_corridor

def expand_cluster(line1, reachable, current_corridor):
    line1.corridor = current_corridor #each line knows its corridor
    while len(corridors) < current_corridor + 1:
        corridors.append([]) #add an empty list if we don't know yet 
    corridors[current_corridor].append(line1) #each corridor knows its line
    while len(reachable) > 0:
        new_candidates = [] 
        for line2 in reachable: 
            
            if line2.visited == False:
                #print "not yet visited l2", line2.name, "called from", line1.name
                line2.visited = True
                sumweight_line2 = 0.
                new_reachable = [] #for 'RegionQuery' (TODO: write separate function)
                for angle in traj_angles:
                    if abs(angle-line2.angle) > max_angle:
                        continue
                    for line3 in traj_angles[angle]:
                        
                        if segments_distance(line2.startx, line2.starty, line2.endx, line2.endy, line3.startx, line3.starty, line3.endx, line3.endy) <= max_dist:
                            sumweight_line2 = sumweight_line2 + line3.weight
                            new_reachable.append(line)
                if sumweight_line2 >= min_density:
                    for line3 in new_reachable:
                        if line3.visited == False:
                            new_candidates.append(line3)
            if line2.corridor < 0:
                line2.corridor = current_corridor
                corridors[current_corridor].append(line2)
        reachable = new_candidates

def rotate_and_print_tuples(xy_tuples, theta):
    if len(xy_tuples) < 2:
        print xy_tuples
        return
    xstart = xy_tuples[0][0]
    ystart = xy_tuples[0][1]
    string = str(xy_tuples[0])
    
    for index in range(1, len(xy_tuples)):
        xend = xy_tuples[index][0]
        yend = xy_tuples[index][1]
        xdiff = xend - xstart
        ydiff = yend - ystart
        newx = xdiff*cos(theta/180*math.pi) - ydiff*sin(theta/180.0*math.pi) + xstart
        newy = xdiff*sin(theta/180*math.pi) + ydiff*cos(theta/180.0*math.pi) + ystart
        string = string + str((newx, newy))
    print string


def  map_best(ys, last_assignments, assignments):
    num_old_assign = max(last_assignments) + 1
    num_new_assign = max(assignmnets) + 1
    
    distances = [[0]*num_old_assign] * num_new_assign
    y_olds = get_weighted_averages(ys, weights, last_assignments)
    y_news = get_weighted_averages(ys, weights, assignments)
    for index1 in range(0, num_new_assign, 1):
        for index2 in range(0, num_old_assign, 1):
            distances[index1][index2] = abs(y_olds[index2] - y_news[index1])
    
    mappings = {}
    for counter in range(0, min(num_old_assign, num_new_assign)):
        smallestd = 1e9
        smallest_new = -1
        smallest_old = -1
        for index1 in range(0, num_new_assign, 1):
            for index2 in range(0, num_old_assign, 1):
                if distances[index1][index2] < smallestd:
                    smallestd = distances[index1][index2]
                    smallest_new = index1
                    smallest_old = index2
        mappings[smallest_old] = smallest_new
        for index1 in range(0, num_new_assign):
            distances[index1][smallest_old] = 1e10
    return mappings


def get_weighted_averages(ys, weights, assignments):
    #print "get_weighted", ys, weights, assignments
    ysums = [0.0] * (max(assignments)+1)
    ycounts = [0] * (max(assignments)+1)
    for index in range(0, len(ys), 1):
        if assignments[index] < 0:
            continue
        ysums[assignments[index]] = ysums[assignments[index]] +  ys[index] * weights[index]
        ycounts[assignments[index]] = ycounts[assignments[index]] + weights[index]
    for index in range(0, len(ysums), 1):
        ysums[index] = ysums[index]  / ycounts[index]
    return ysums


def expand_dense_bylist(ys, angles, weights, maxd, minw, max_angle, point_index, visited, reachable, clus, assignments):
    """ """
    #print "visited", visited
    #print "reachable", reachable
    #print "ys", ys, "angles", angles
    assignments[point_index] = clus
    while len(reachable) > 0:
        next_reachable = []        
        for point_index2 in reachable:
            candidate_reachable = []
            sumw = 0.
            if visited[point_index2] == False:
                visited[point_index2] = True
                for point_index3 in range(0, len(ys), 1):
                    if ys[point_index3] == None:
                        continue
                    if abs(ys[point_index3] - ys[point_index2]) < maxd and abs(angles[point_index3] - angles[point_index2]) < max_angle:
                        sumw = sumw + weights[point_index3]
                        if not visited[point_index3]:
                            candidate_reachable.append(point_index3)
                if sumw >= minw:
                    next_reachable.extend(candidate_reachable)
            if assignments[point_index2] < 0:
                assignments[point_index2] = clus
        reachable = next_reachable

def DBScan_bylist(x, ys, angles, weights, maxd, minw, max_angle):
    """ Take as input a common x coordinate, and lists y coordinates, angles and weights of points to be clustered, values should be set to None for those that are not to be included
    output is list of cluster ids, starting from 0, with -1 for not belonging to a cluster (either input was None or the point was not in region satisfying density requirement"""
    #print "by_list", x, ys, angles, weights, maxd, minw, max_angle
    clus = 0
    visited = [False] * len(ys)
    assignments = [-2] * len(ys)

    for point_index in range(0, len(ys), 1):

        if visited[point_index] or ys[point_index] == None:
            continue
        visited[point_index] = True
        reachable = []
        sumw = 0.
        for point_index2 in range(0, len(ys), 1):
     #       print "comparing point to point", point_index, point_index2, ys[point_index], ys[point_index2];
            if abs(ys[point_index] - ys[point_index2]) < maxd and abs(angles[point_index] - angles[point_index2]) < max_angle:
                sumw = sumw + weights[point_index2]
                reachable.append(point_index2)
        if sumw > minw:
            expand_dense_bylist(ys, angles, weights, maxd, minw, max_angle, point_index, visited, reachable, clus, assignments) 
            clus = clus + 1
        else :
            assignments[point_index] = -1
    #print "sub clustering", x, assignments
    return assignments




#main program, need to add main function

#file IO: needs to be in function
# Read file instantiate trajectories, add to dictionary of angles
infile = sys.argv[1]
max_dist = float(sys.argv[2])
min_density = float(sys.argv[3])
max_angle = float(sys.argv[4])

# For each line, get candidate lines from angle dictionary, find within distance
traj_angles = defaultdict(list) #look up angles fast, each angle (in degrees) will have a list of Trajectory objects
trajectories = [] # list of trajectories, keep it? 
fh = open (infile, 'r') 
for line in fh:
    linelist = line.split();
    traj = Trajectory(name=linelist[0], weight = float(linelist[1]), startx=float(linelist[2]), starty=float(linelist[3]), endx=float(linelist[4]), endy=float(linelist[5]))
    rounded_angle = round_to(traj.angle, 0.5);
    traj_angles[rounded_angle].append(traj) #add the trajectory to a list in the dictionary of angles
    trajectories.append(traj)



current_corridor = 0
for line in trajectories:
    current_corridor = DBScan(line, traj_angles, current_corridor)
    print line.name, line.corridor #print it to a file!



# for each corridor, find the weighted average angle, rotate every
# line by this angle to be approximately parallel to the x axis
# for each x, find the y for each of the rotated lines and do a DB-Scan with 
# this set of ys (some of them might be None if the rotated line does not
# contain this x)
# rotate the set of lines back and output the corridors
for corridor in range(0, len(corridors)):
    w_sumangle = 0.
    sum_weight = 0
    first = True
    last_assignments = []
    angles = []
    weights = []
    line_stack = []
    minx_start = sys.float_info.max #first x we will consider
    maxx_rotated_end = sys.float_info.min #last x we will consider
    for line in corridors[corridor]: #weighted average of angles
        w_sumangle = w_sumangle + line.angle * line.weight
        sum_weight = sum_weight + line.weight
        angles.append(line.angle)
        weights.append(line.weight)
        if minx_start > line.startx:
            minx_start = line.startx
    rot_angle = w_sumangle / sum_weight
    for line in corridors[corridor]:
        line.rotate(-rot_angle)
        if maxx_rotated_end <  line.endx_rotated:
            maxx_rotated_end = line.endx_rotated
    for x in arange(minx_start, maxx_rotated_end, step_size ):
        #print "arange", x, minx_start, maxx_rotated_end, step_size
        ys = []
        for line in corridors[corridor]:
            ys.append(line.getY_rotated(x))
        #print "ys", ys
        assignments = DBScan_bylist(x, ys, angles, weights, max_dist, min_density, max_angle)
        #assigments is list of integers representing corridor assignment

        #print "Assigned!", assignments
        if assignments != last_assignments:
            yaves  = get_weighted_averages(ys, weights, assignments)
            if first:

                for idx, val in enumerate(yaves):
                    line_stack.append([])
                    line_stack[idx].append((x, yaves[idx]))
            else:
                best_mapped = map_best(ys, last_assignments, assignments)
                
                temp_stack = []
                new_assignment_mapped = {}
                for old_sub_corr in best_mapped.keys:
                    if old_sub_corr not in best_mapped:
                        rotate_and_print_tuples(line_stack[old_sub_corr], rot_angle)
                        continue
                    new_sub_corr = best_mapped[old_sub_corr]
                    temp_stack[new_sub_corr] = line_stack[old_sub_corr]
                    temp_stack[new_sub_corr].append(x, yaves[new_sub_corr])
                    new_assignment_mapped[new_sub_corr] = True
                for new_sub_corr in range(0, max(assignments)+1):
                    if not new_assignment_mapped[new_sub_corr]:
                        temp_stack[new_sub_corr] = []
                        temp_stack[new_sub_corr].append(x, yaves[new_sub_corr])
                line_stack = temp_stack
            last_assignments = assignments
        elif x + step_size > maxx_rotated_end: #last one
     
            yaves  = get_weighted_averages(ys, weights, assignments)
            for idx, val in enumerate(yaves):
                line_stack[idx].append((x, yaves[idx]))
                rotate_and_print_tuples(line_stack[idx], rot_angle)







