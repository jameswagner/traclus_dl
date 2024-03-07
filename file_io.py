from collections import defaultdict
from trajectory import Trajectory, TrajectorySegment
from typing import List, Dict, Optional

def round_to(n, precision):
    return round(n / precision) * precision

def read_file(infile: str, segment_size: float) -> tuple[List[Trajectory], Dict[float, List[Trajectory]]]:
    """
    Reads trajectory data from the input file.

    Args:
        infile: Path to the input data file.
        segment_size: Size of segments to create from trajectories.

    Returns:
        A tuple containing:
            - trajectories: A list of Trajectory objects.
            - traj_angles: A dictionary mapping angles (rounded to specific precision) to lists of Trajectory objects.
    """

    traj_angles = defaultdict(list)  # Look up angles quickly
    trajectories = []

    with open(infile, 'r') as fh:
        for line in fh:
            if line.startswith("#"):
                continue

            linelist = line.split()
            traj = Trajectory(
                name=linelist[0], weight=float(linelist[1]),
                start_x=float(linelist[2]), start_y=float(linelist[3]),
                end_x=float(linelist[4]), end_y=float(linelist[5])
            )
            traj.make_segments(segment_size)
            rounded_angle = round_to(traj.angle, 0.01)  # Replace with desired rounding precision
            traj_angles[rounded_angle].append(traj)  # Add trajectory to angle in dictionary
            trajectories.append(traj)

    return trajectories, traj_angles

def print_weighted_averages(cluster_segments, corr_number, output_file_handle):
    """File output method for printing weighted average of start and ends for the segments assigned to that cluster. File format is designed for visualization with QVis"""
    weightsum = 0.
    x1sum = 0.
    y1sum = 0.
    x2sum = 0.
    y2sum = 0.
    for segment in cluster_segments:
        weightsum += segment.parent_trajectory.weight
        x1sum += segment.start_x * segment.parent_trajectory.weight
        x2sum += segment.end_x * segment.parent_trajectory.weight
        y1sum += segment.start_y * segment.parent_trajectory.weight
        y2sum += segment.end_y * segment.parent_trajectory.weight
    output_file_handle.write(str(corr_number) + "\t"+  str(weightsum) + "\tLINESTRING(" + str(x1sum/weightsum) + " "+ str(y1sum/weightsum) + ", " + str(x2sum/weightsum) + " " + str(y2sum/weightsum) + ")\n")


def write_segment_output(trajectories: List[Trajectory], corridors: List[List[TrajectorySegment]], segment_out_filename: str, corridor_out_filename: str) -> None:
    """
    Writes segment data to specific files based on corridor ID.

    Args:
        segments: A list of TrajectorySegment objects.
        corridors: A list of lists corresponding to corridor assignments of corridors.
        infile: Base name of the input file (used for output file naming).
    """
    with open(segment_out_filename, "w") as segment_file_handle:
        segment_file_handle.write("id\tweight\tangle\tcorridor_id\tcoordinates\n")
        for trajectory in trajectories:
            for segment in trajectory.segments:
                segment_file_handle.write(
                    f"{segment.id}\t{segment.parent_trajectory.weight}\t"
                    f"{segment.parent_trajectory.angle}\t{segment.corridor}\t" 
                    f"LINESTRING({segment.start_x} {segment.start_y}, {segment.end_x} {segment.end_y})\n"
                )

    with open(corridor_out_filename, "w") as corridor_file_handle:
        corridor_file_handle.write("name\tweight\tcoordinates\n")
        for idx, corridor in enumerate(corridors):
            print_weighted_averages(corridor, idx, corridor_file_handle)