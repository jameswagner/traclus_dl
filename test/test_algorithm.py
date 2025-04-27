#!/usr/bin/env python3
"""
Test script for Traclus_DL with simple test data.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test data path
test_data_path = os.path.join(project_root, "data", "simple_test_data.txt")

def test_clustering():
    """
    Test the basic clustering functionality with a simple dataset.
    """
    from src.trajectory import Trajectory
    from src.file_io import read_file
    from src.Traclus_DL import build_queue, pop_corridors_from_queue, segment_to_line_dist, segment_to_line_closest_seg
    
    # Parameters for simple test
    max_dist = 5.0       # Trajectories within 5 units should be grouped
    min_density = 3.0    # Need at least 3 trajectories to form a corridor
    max_angle = 5.0      # 5 degrees tolerance for considering parallel trajectories
    segment_size = 20.0  # Segment size for splitting trajectories
    
    print(f"Testing Traclus_DL with simple data...")
    print(f"Parameters: max_dist={max_dist}, min_density={min_density}, max_angle={max_angle}, segment_size={segment_size}")
    
    # Read test data
    try:
        trajectories, traj_angles = read_file(test_data_path, segment_size)
        print(f"Read {len(trajectories)} trajectories")
        
        # Print basic trajectory info
        print("\nTrajectory summary:")
        for i, traj in enumerate(trajectories):
            print(f"  {i+1}. {traj.name}: ({traj.start_x}, {traj.start_y}) → ({traj.end_x}, {traj.end_y}), " +
                  f"angle: {traj.angle:.1f}°, length: {traj.length:.1f}, segments: {len(traj.segments)}")
            
        # Build priority queue of clusters
        print("\nBuilding clusters...")
        pq = build_queue(
            trajectories, traj_angles, max_dist, min_density, max_angle,
            segment_to_line_dist, segment_to_line_closest_seg
        )
        
        # Extract corridors
        print("\nExtracting corridors...")
        corridors = pop_corridors_from_queue(pq)
        
        # Analyze results
        print("\nResults:")
        print(f"Found {len(corridors)} corridors")
        
        for i, corridor in enumerate(corridors):
            # Group by original trajectory to see which trajectories contributed to this corridor
            corridor_trajs = {}
            for segment in corridor:
                traj_name = segment.parent_trajectory.name
                if traj_name not in corridor_trajs:
                    corridor_trajs[traj_name] = 1
                else:
                    corridor_trajs[traj_name] += 1
            
            # Get a representative trajectory to determine direction
            rep_traj = corridor[0].parent_trajectory
            
            print(f"\nCorridor {i+1}:")
            print(f"  Direction: {rep_traj.angle:.1f}° (approximately {get_direction_name(rep_traj.angle)})")
            print(f"  Contains {len(corridor)} segments from {len(corridor_trajs)} trajectories:")
            for traj_name, count in corridor_trajs.items():
                print(f"    - {traj_name}: {count} segments")
        
        print("\nTest completed successfully!")
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return False

def get_direction_name(angle):
    """Convert angle in degrees to a cardinal direction name."""
    angle = angle % 360
    if angle < 22.5 or angle >= 337.5:
        return "East"
    elif angle < 67.5:
        return "Northeast"
    elif angle < 112.5:
        return "North"
    elif angle < 157.5:
        return "Northwest"
    elif angle < 202.5:
        return "West"
    elif angle < 247.5:
        return "Southwest"
    elif angle < 292.5:
        return "South"
    else:
        return "Southeast"

def run_full_test_with_visualization():
    """
    Run the full algorithm and generate visualization.
    """
    # Run the algorithm 
    from src.Traclus_DL import main
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    
    sys.argv = [
        "traclus_dl",  # Program name
        "--infile", test_data_path,
        "--max_dist", "5",
        "--min_density", "3",
        "--max_angle", "5",
        "--segment_size", "20"
    ]
    
    print("Running full algorithm...")
    main()  # This will generate the output files
    
    # Now generate visualization similar to visualize_results.py but integrated
    print("\nGenerating visualization...")
    
    # Parse files from visualize_results.py logic
    from pathlib import Path
    base_name = os.path.basename(test_data_path)
    segment_files = list(Path(".").glob(f"{base_name}*.segmentlist.txt"))
    corridor_files = list(Path(".").glob(f"{base_name}*.corridorlist.txt"))
    
    if not segment_files or not corridor_files:
        print("Error: Could not find output files.")
        return False
    
    # Use the most recent files
    segment_file = sorted(segment_files)[-1]
    corridor_file = sorted(corridor_files)[-1]
    
    print(f"Using segment file: {segment_file}")
    print(f"Using corridor file: {corridor_file}")
    
    # Import visualization functions
    sys.path.insert(0, str(project_root))
    try:
        from visualize_results import (
            parse_trajectory_file, 
            parse_corridor_file, 
            parse_segment_file, 
            visualize_results
        )
        
        # Parse files
        trajectories = parse_trajectory_file(test_data_path)
        corridors = parse_corridor_file(corridor_file)
        segments = parse_segment_file(segment_file)
        
        print(f"Found {len(trajectories)} trajectories, {len(corridors)} corridors, and {len(segments)} segments")
        
        # Create visualization
        fig = visualize_results(trajectories, corridors, segments)
        
        # Save figure
        output_file = os.path.join(project_root, "clustering_result.png")
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {output_file}")
        
        plt.show()
        return True
    except Exception as e:
        print(f"Visualization error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--visualize":
        run_full_test_with_visualization()
    else:
        test_clustering() 