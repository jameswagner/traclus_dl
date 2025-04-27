#!/usr/bin/env python3
"""
Visualization script for Traclus_DL results.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def parse_trajectory_file(filename):
    """Parse raw trajectory input file."""
    trajectories = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split()
            if len(parts) >= 6:
                traj = {
                    'name': parts[0],
                    'weight': float(parts[1]),
                    'start_x': float(parts[2]),
                    'start_y': float(parts[3]),
                    'end_x': float(parts[4]),
                    'end_y': float(parts[5])
                }
                trajectories.append(traj)
                
    return trajectories

def parse_corridor_file(filename):
    """Parse corridor output file."""
    corridors = []
    
    with open(filename, 'r') as f:
        # Skip header
        next(f, None)
        
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) >= 3:
                corridor_id = int(parts[0])
                weight = float(parts[1])
                
                # Parse LINESTRING format: LINESTRING(x1 y1, x2 y2)
                coords_str = parts[2].replace('LINESTRING(', '').replace(')', '')
                point_strs = coords_str.split(',')
                
                start_coords = [float(x) for x in point_strs[0].strip().split()]
                end_coords = [float(x) for x in point_strs[1].strip().split()]
                
                corridor = {
                    'id': corridor_id,
                    'weight': weight,
                    'start_x': start_coords[0],
                    'start_y': start_coords[1],
                    'end_x': end_coords[0],
                    'end_y': end_coords[1]
                }
                corridors.append(corridor)
                
    return corridors

def parse_segment_file(filename):
    """Parse segment output file with corridor assignments."""
    segments = []
    
    with open(filename, 'r') as f:
        # Skip header
        next(f, None)
        
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) >= 5:
                segment_id = parts[0]
                weight = float(parts[1])
                angle = float(parts[2])
                corridor_id = int(parts[3])
                
                # Parse LINESTRING format
                coords_str = parts[4].replace('LINESTRING(', '').replace(')', '')
                point_strs = coords_str.split(',')
                
                start_coords = [float(x) for x in point_strs[0].strip().split()]
                end_coords = [float(x) for x in point_strs[1].strip().split()]
                
                segment = {
                    'id': segment_id,
                    'weight': weight,
                    'angle': angle,
                    'corridor_id': corridor_id,
                    'start_x': start_coords[0],
                    'start_y': start_coords[1],
                    'end_x': end_coords[0],
                    'end_y': end_coords[1]
                }
                segments.append(segment)
                
    return segments

def visualize_results(trajectories, corridors, segments):
    """Create a visualization of the original trajectories and found corridors."""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Get a list of colors for corridors
    colors = list(mcolors.TABLEAU_COLORS.values())
    
    # Plot original trajectories (light gray)
    for traj in trajectories:
        ax.plot(
            [traj['start_x'], traj['end_x']], 
            [traj['start_y'], traj['end_y']], 
            'lightgray', linewidth=1, alpha=0.5
        )
        
    # Plot segments colored by corridor assignment
    corridor_segments = {}
    for segment in segments:
        corridor_id = segment['corridor_id']
        if corridor_id >= 0:  # -1 means no assignment
            if corridor_id not in corridor_segments:
                corridor_segments[corridor_id] = []
            corridor_segments[corridor_id].append(segment)
    
    for corridor_id, segs in corridor_segments.items():
        color = colors[corridor_id % len(colors)]
        for segment in segs:
            ax.plot(
                [segment['start_x'], segment['end_x']], 
                [segment['start_y'], segment['end_y']], 
                color=color, linewidth=1, alpha=0.5
            )
    
    # Plot the corridors (thicker lines)
    for i, corridor in enumerate(corridors):
        color = colors[i % len(colors)]
        ax.plot(
            [corridor['start_x'], corridor['end_x']], 
            [corridor['start_y'], corridor['end_y']], 
            color=color, linewidth=3
        )
        
        # Add corridor label at midpoint
        mid_x = (corridor['start_x'] + corridor['end_x']) / 2
        mid_y = (corridor['start_y'] + corridor['end_y']) / 2
        ax.text(mid_x, mid_y, f"Corridor {corridor['id']}", 
                fontsize=10, ha='center', va='center',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
    
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('Trajectory Clustering Results')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add legend
    legend_entries = []
    legend_labels = []
    
    # Add a gray line for original trajectories
    legend_entries.append(plt.Line2D([0], [0], color='lightgray', lw=1))
    legend_labels.append('Original Trajectories')
    
    # Add a line for each corridor
    for i in range(len(corridors)):
        color = colors[i % len(colors)]
        legend_entries.append(plt.Line2D([0], [0], color=color, lw=3))
        legend_labels.append(f'Corridor {i}')
    
    ax.legend(legend_entries, legend_labels, loc='best')
    
    plt.tight_layout()
    return fig

def main():
    parser = argparse.ArgumentParser(description='Visualize Traclus_DL results')
    parser.add_argument('--input', required=True, help='Original trajectory input file')
    parser.add_argument('--output', default='clustering_result.png', help='Output image file')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    base_name = input_path.name
    data_dir = project_root / 'data'
    
    # Look in multiple locations for output files
    search_paths = [
        Path("."),          # Current directory
        data_dir,           # Data directory
        input_path.parent,  # Directory containing the input file
    ]
    
    segment_files = []
    corridor_files = []
    
    for path in search_paths:
        segment_files.extend(list(path.glob(f"{base_name}*.segmentlist.txt")))
        corridor_files.extend(list(path.glob(f"{base_name}*.corridorlist.txt")))
    
    if not segment_files or not corridor_files:
        print(f"Error: Could not find output files. Run Traclus_DL first.")
        print(f"Searched in: {', '.join(str(p) for p in search_paths)}")
        return 1
    
    # Use the most recent files
    segment_file = sorted(segment_files)[-1]
    corridor_file = sorted(corridor_files)[-1]
    
    print(f"Using segment file: {segment_file}")
    print(f"Using corridor file: {corridor_file}")
    
    # Parse files
    trajectories = parse_trajectory_file(args.input)
    corridors = parse_corridor_file(corridor_file)
    segments = parse_segment_file(segment_file)
    
    print(f"Found {len(trajectories)} trajectories, {len(corridors)} corridors, and {len(segments)} segments")
    
    # Create visualization
    fig = visualize_results(trajectories, corridors, segments)
    
    # Save figure
    fig.savefig(args.output, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {args.output}")
    
    plt.show()
    return 0

if __name__ == "__main__":
    sys.exit(main()) 