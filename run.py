#!/usr/bin/env python3
"""
Main runner script for Traclus_DL.

Usage:
  python run.py --infile data/simple_test_data.txt --max_dist 5 --min_density 3 --max_angle 5 --segment_size 20
"""

import sys
import os
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Pass control to the main function in Traclus_DL
from src.Traclus_DL import main

if __name__ == "__main__":
    sys.exit(main()) 