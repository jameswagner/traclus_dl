from Trajectory import *
import sys
from collections import defaultdict

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
    if line1.visited == True or line1.corridor>=0:
        return current_corridor
    reachable = []
    line1.visited = True
    sumweight = 0.0
    for angle in traj_angles:

        if abs(angle-line1.angle) > max_angle:
            continue

        for line2 in traj_angles[angle]:
            
            if segments_distance(line1.startx, line1.starty, line1.endx, line1.endy, line2.startx, line2.starty, line2.endx, line2.endy) <= max_dist:
                reachable.append(line2)
                sumweight = sumweight + line2.weight
                
    print reachable, sumweight            
    if sumweight < min_density:
        line1.corridor = -1
        return current_corridor
    else:
        expand_cluster(line1, reachable, current_corridor)
        current_corridor = current_corridor + 1
        return current_corridor

def expand_cluster(line1, reachable, current_corridor):
    line1.corridor = current_corridor
    while len(corridors) < current_corridor + 1:
        corridors.append([])
    corridors[current_corridor].append(line1)
    while len(reachable) > 0:
        new_candidates = []
        for line2 in reachable:
            
            if line2.visited==False:
                print "not yet visited l2", line2.name, "called from", line1.name
                line2.visited=True
                sumweight_line2 = 0.
                for angle in traj_angles:
                    if abs(angle-line2.angle) > max_angle:
                        continue
                    for line3 in traj_angles[angle]:
                        
                        if segments_distance(line2.startx, line2.starty, line2.endx, line2.endy, line3.startx, line3.starty, line3.endx, line3.endy) <= max_dist:
                            sumweight_line2 = sumweight_line2 + line3.weight
                            if line3.visited == False:
                                print "considering", line3.name
                                new_candidates.append(line3)
            if line2.corridor < 0:
                line2.corridor = current_corridor
                corridors[current_corridor].append(line2)
        reachable = new_candidates




# Read file instantiate trajectories, add to dictionary of angles
infile = sys.argv[1]
max_dist = float(sys.argv[2])
min_density = float(sys.argv[3])
max_angle = float(sys.argv[4])

# For each line, get candidate lines from angle dictionary, find within distance
traj_angles = defaultdict(list)
trajectories = []
fh = open (infile, 'r')
for line in fh:
    linelist = line.split();
    traj = Trajectory(name=linelist[0], weight = float(linelist[1]), startx=float(linelist[2]), starty=float(linelist[3]), endx=float(linelist[4]), endy=float(linelist[5]))
    rounded_angle = round_to(traj.angle, 0.5);
    traj_angles[rounded_angle].append(traj)
    trajectories.append(traj)



current_corridor=0
for line in trajectories:
    current_corridor = DBScan(line, traj_angles,current_corridor)





for corridor in range(0, len(corridors)):
    w_sumangle = 0.
    sum_weight = 0.
    minx_start = sys.float_info.max
    maxx_rotated_end = sys.float_info.min
    for line in corridors[corridor]:
        w_sumangle = w_sumangle + line.angle * line.weight
        sum_weight = sum_weight + line.weight
        if minx_start > line.startx:
            minx_start = line.startx
    rot_angle = w_sumangle / sum_weight
    for line in corridors[corridor]:
        line.rotate(rot_angle)
        if maxx_rotated_end <  endx_rotated:
            maxx_rotated_end = endx_rotated








    



