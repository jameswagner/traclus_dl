# Traclus_dl

Traclus_dl is a program inspired by Traclus (Trajectory Clustering: A partition and group framework, published by Lee et al in 2007 in ACM SIGMOD)
designed for desire lines consisting of origin-destination pairs in two dimensions.

## Project Structure

```
traclus_dl/
├── data/              # Input data files
├── src/               # Source code
├── test/              # Test scripts
├── requirements.txt   # Dependencies
├── README.md          # This file
└── run.py             # Main entry point
```

## Input Format
 
The input is a file with each line consisting of one desire line, space or tab separated. 
Each line should have the following format:
```
line_id weight start_x start_y end_x end_y
```
Where:
- `line_id`: Identifier for the desire line.
- `weight`: Numeric value indicating the weight of the desire line.
- `start_x, start_y`: Starting coordinates of the desire line.
- `end_x, end_y`: Ending coordinates of the desire line.

Example input file (`data/simple_test_data.txt`):
```
east1 10.0 0.0 0.0 100.0 0.0
east2 10.0 0.0 1.0 100.0 1.0
east3 10.0 0.0 2.0 100.0 2.0
```

## Output

The algorithm produces two output files in the same directory as the input file:
- `<filename>.<max_dist>.<min_density>.<max_angle>.<segment_size>.segmentlist.txt`: Contains information about the trajectory segments and their corridor assignments.
- `<filename>.<max_dist>.<min_density>.<max_angle>.<segment_size>.corridorlist.txt`: Contains the identified corridors.

These files can be readily visualized using the included visualization tool or imported into QGIS.

## Running the Program

### Setup
The software is written in Python and can be run from the command line where Python is installed.

```
# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Windows/PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Running the Algorithm
Use the following command:
```
python run.py --infile <filename> --max_dist <max_dist> --min_density <min_density> --max_angle <max_angle> --segment_size <segment_size>
```

Where:
- `filename`: Path to the input file
- `max_dist`: Maximum distance parameter for the DBScan algorithm
- `min_density`: Minimum density parameter for the DBScan algorithm
- `max_angle`: Maximum angle parameter for the DBScan algorithm
- `segment_size`: Segment size parameter for the DBScan algorithm

Example usage:
```
python run.py --infile data/simple_test_data.txt --max_dist 5 --min_density 3 --max_angle 5 --segment_size 20
```

### Running Tests and Visualization

To run a basic test with the simple test data:
```
python test/test_algorithm.py
```

To visualize the results after running the algorithm:
```
# First run the algorithm to generate output files
python run.py --infile data/simple_test_data.txt --max_dist 5 --min_density 3 --max_angle 5 --segment_size 20

# Then visualize the results
python test/visualize.py --input data/simple_test_data.txt
```

The visualization tool will automatically search for the output files in the current directory, the data directory, and the directory containing the input file. The visualization will be saved as `clustering_result.png` by default.

## Algorithm

Traclus_dl implements a modified version of the Traclus algorithm specifically designed for origin-destination pairs. The algorithm:

1. Segments each trajectory into smaller pieces
2. Clusters similar segments based on angle, distance, and density constraints
3. Uses a priority queue to identify corridors in order of their weights
4. Outputs corridors as weighted averaged line segments for visualization 

## Dependencies

- Python 3.6+
- NumPy
- Matplotlib

See `requirements.txt` for specific versions.

## Citation

If you use this implementation in your research, please cite:

Bahbouh, K., Wagner, J. R., Morency, C., & Berdier, C. (2015). TraClus-DL: A Desire Line Clustering Framework to Identify Demand Corridors. *Transportation Research Board 94th Annual Meeting*. Washington DC, United States. Paper No. 15-3508.

[https://trid.trb.org/View/1338139](https://trid.trb.org/View/1338139)