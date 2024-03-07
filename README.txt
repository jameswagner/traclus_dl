Traclus_dl

Traclus_dl is a program inspired by Traclus (Trajectory Clustering: A partition and group framework, published by Lee et al in 2007 in ACM SIGMOD)
 designed for desire lines consisting of origin-destination pairs in two dimensions.
 
Input Format
 
The input is a file with each line consisting of one desire line, space or tab separated. 
Each line should have the following format:
line_id weight start_x start_y end_x end_y
line_id: Identifier for the desire line.
weight: Numeric value indicating the weight of the desire line.
start_x, start_y: Starting coordinates of the desire line.
end_x, end_y: Ending coordinates of the desire line.

Example input file (test_data1.txt):

1 10.0 0.0 0.0 5.0 5.0
2 15.0 2.0 2.0 7.0 7.0
3 8.0 10.0 10.0 15.0 15.0

Output:

The output will be a set of corridors or segment clusters, which can be readily visualized in the open-source QGIS program. 
Additionally, a separate file will be generated identifying the corridor number each segment was assigned to (-1 for no segment).

Running the Program

The software is written in Python and can be run from the command line where Python is installed. 
Use the following command:
python Traclus_DL.py --infile <filename> --max_dist <max_dist> --min_density <min_density> --max_angle <max_angle> --segment_size <segment_size>
filename: Path to the input file
max_dist: Maximum distance parameter for the DBScan algorithm
min_density: Minimum density parameter for the DBScan algorithm
max_angle: Maximum angle parameter for the DBScan algorithm
segment_size: Segment size parameter for the DBScan algorithm

Example usage:
python Traclus_DL.py --infile test_data1.txt --max_dist 100 --min_density 4 --max_angle 1 --segment_size 12

This command will process the desire lines in test_data1.txt with the specified parameters and generate the output files for visualization.
