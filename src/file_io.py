from collections import defaultdict
import os
from .trajectory import Trajectory, TrajectorySegment
from typing import List, Dict, Optional, Tuple

def round_to(n: float, precision: float) -> float:
    """
    Round a number to a specific precision.
    
    Args:
        n: Number to round
        precision: Precision to round to
        
    Returns:
        Rounded number
    """
    return round(n / precision) * precision

def read_file(infile: str, segment_size: float) -> Tuple[List[Trajectory], Dict[float, List[Trajectory]]]:
    """
    Reads trajectory data from the input file.

    Args:
        infile: Path to the input data file.
        segment_size: Size of segments to create from trajectories.

    Returns:
        A tuple containing:
            - trajectories: A list of Trajectory objects.
            - traj_angles: A dictionary mapping angles (rounded to specific precision) to lists of Trajectory objects.
            
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the input file has invalid format
    """
    traj_angles = defaultdict(list)  # Look up angles quickly
    trajectories = []

    if not os.path.exists(infile):
        raise FileNotFoundError(f"Input file not found: {infile}")

    with open(infile, 'r') as fh:
        for line_number, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                linelist = line.split()
                if len(linelist) < 6:
                    raise ValueError(f"Line {line_number} has fewer than 6 fields: {line}")
                
                traj = Trajectory(
                    name=linelist[0], weight=float(linelist[1]),
                    start_x=float(linelist[2]), start_y=float(linelist[3]),
                    end_x=float(linelist[4]), end_y=float(linelist[5])
                )
                traj.make_segments(segment_size)
                rounded_angle = round_to(traj.angle, 0.01)  # Angle precision of 0.01 degrees
                traj_angles[rounded_angle].append(traj)  # Add trajectory to angle in dictionary
                trajectories.append(traj)
            except (ValueError, IndexError) as e:
                raise ValueError(f"Error parsing line {line_number}: {line}. {str(e)}")

    if not trajectories:
        raise ValueError(f"No valid trajectories found in file: {infile}")
        
    return trajectories, traj_angles

def print_weighted_averages(cluster_segments: List[TrajectorySegment], corr_number: int, output_file_handle) -> None:
    """
    Calculate and write weighted average of start and end points for segments assigned to a cluster.
    File format is designed for visualization with QGIS.
    
    Args:
        cluster_segments: List of segments in the cluster
        corr_number: Corridor number
        output_file_handle: File handle to write to
    """
    if not cluster_segments:
        return
        
    weightsum = 0.0
    x1sum = 0.0
    y1sum = 0.0
    x2sum = 0.0
    y2sum = 0.0
    
    for segment in cluster_segments:
        weightsum += segment.parent_trajectory.weight
        x1sum += segment.start_x * segment.parent_trajectory.weight
        x2sum += segment.end_x * segment.parent_trajectory.weight
        y1sum += segment.start_y * segment.parent_trajectory.weight
        y2sum += segment.end_y * segment.parent_trajectory.weight
        
    if weightsum > 0:
        output_file_handle.write(f"{corr_number}\t{weightsum}\tLINESTRING({x1sum/weightsum} {y1sum/weightsum}, {x2sum/weightsum} {y2sum/weightsum})\n")


def write_segment_output(trajectories: List[Trajectory], corridors: List[List[TrajectorySegment]], 
                         segment_out_filename: str, corridor_out_filename: str) -> None:
    """
    Writes segment data to output files for corridor visualization.

    Args:
        trajectories: A list of Trajectory objects.
        corridors: A list of lists corresponding to corridor assignments.
        segment_out_filename: Path to the segment output file.
        corridor_out_filename: Path to the corridor output file.
        
    Raises:
        OSError: If there is an error writing to the output files
    """
    try:
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
                
        print(f"Output written to {segment_out_filename} and {corridor_out_filename}")
    except OSError as e:
        raise OSError(f"Error writing output files: {str(e)}")