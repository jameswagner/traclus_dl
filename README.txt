Traclus_dl is a program inspired by Traclus (Trajectory Clustering: A partition and group framework, published by Lee et al in 2007
in ACM SIGMOD) designed for desire lines consisting of origin-destination pairs in two dimensions.

The input is a file with each line consisting of one desire line, space or tab separated. Each line will have
a line identified, followed by a weight, start x position, start y position, end x and end y. 

The output will be a set of corridors or segment clusters, which can be readily visualized in the open source QGis program, as well as
a separate file identifying the corridor number each segment was assigned to (-1 for no segment). Software is written in python 
and can be run from the command line where Python is installed as "python Traclus_DL.py <filename> <max_dist> <min_density> <max_angle> <segment_size>
where filename is the input file path, and max_dist, min_density, max_angle and segment_size are other parameters for the DBScan algorithm.



