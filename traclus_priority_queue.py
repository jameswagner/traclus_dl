from heapq import heappop, heappush
from math import hypot
from collections import defaultdict
from typing import Dict, List, Sequence, Set, Tuple
from trajectory import TrajectorySegment

class ClusterEntry:
    def __init__(self, priority: float,  cluster_seed: TrajectorySegment, cluster: Sequence[TrajectorySegment], removed: bool) -> None:
        self.priority: float = priority
        self.cluster_seed: TrajectorySegment = cluster_seed
        self.cluster: Sequence[TrajectorySegment] = cluster
        self.removed: bool = removed
    
    # Define __lt__ to ensure correct comparison of ClusterEntry objects
    # This is reversed (uses >) to ensure that the highest priority is popped first
    def __lt__(self, other):
        return self.priority > other.priority


class TraclusPriorityQueue:
    """This is an implementation of a priority queue as needed for Traclus_DL.
    After running the DBScan with a particular segment, we will have a cluster of segments
    with a given sum of weights and a sum of squares of distances. If this cluster
    sum of weights reaches the minimum, this will be added to the queue.
    When it comes time to pop the queue, typically after all segments in the dataset have been 
    considered, those with the highest sum of weights will be considered first. As a tie-breaker 
    the sum of squares distances is considered, with those having the smallest sum of squares 
    (eg "tighter" clusters being considered first) segments are being kept track of with the 
    to_removed set to ensure that once they have been popped they are not considered again if a 
    lower priority cluster is reached and found to contain segments already popped for a 
    higher cluster, then the cluster will either be removed altogether if it falls below the minimum 
    weight sum threshold or re-added with a lower threshold if it is >= the minimum threshold"""

    def __init__(self, min_weight: float) -> None:
        self.min_weight: float = min_weight
        self.pq: List[ClusterEntry] = []  # list of entries arranged in a heap
        self.entry_finder: Dict[TrajectorySegment, ClusterEntry] = {}  # mapping of segments to entries
        self.processed_segments: Set[TrajectorySegment] = set()
        
    def add_cluster(self, cluster_seed: TrajectorySegment, cluster: Sequence[TrajectorySegment], priority: float) -> None:
        """Add a new cluster or (lazily remove any existing cluster with the same seed)"""
        if cluster_seed in self.entry_finder:
            self.remove_cluster(cluster_seed)
        entry: ClusterEntry = ClusterEntry(priority, cluster_seed, cluster, False)
        self.entry_finder[cluster_seed] = entry
        heappush(self.pq, entry)
        
    def remove_cluster(self, cluster_seed: TrajectorySegment) -> None:
        """Lazily Mark an existing cluster as removed. Raise KeyError if not found."""
        entry: ClusterEntry = self.entry_finder.pop(cluster_seed)
        entry.removed = True

    def pop_cluster(self) ->  Sequence[TrajectorySegment]:
        """Remove and return the cluster with the highest priority. Check that 
        Raise KeyError if the queue is empty."""

        while self.pq:
            entry: ClusterEntry = heappop(self.pq)
            if not entry.removed:
                processed_segments: Sequence[TrajectorySegment] = [seg for seg in entry.cluster if seg in self.processed_segments]
                if not processed_segments:
                    for segment in entry.cluster:
                        self.processed_segments.add(segment)
                    return entry.cluster
                unprocessed_segments: Sequence[TrajectorySegment] = [seg for seg in entry.cluster if seg not in self.processed_segments]
                unprocessed_weight: float = sum([seg.weight for seg in entry.cluster if seg not in self.processed_segments])
                if unprocessed_weight >= self.min_weight:
                    entry.cluster = unprocessed_segments
                    entry.priority = unprocessed_weight
                    heappush(self.pq, entry)
                else:
                    continue
        return []

    def sum_pairwise(self, segments):
        """For a set of segments, returns the sum of distances for the set of all pairs of start 
        points, when building corridors in a greedy fashion, the program sorts candidate corridors 
        in decreasing order of the sum of their weights, and starts with the corridor having 
        the highest weight. In cases of ties, "tighter" corridors (i.e. their constituent 
        segments are closer together) given priority. This is the function used to determine the 
        pairwise sum of squares of the member segments (note that weight is not considered)
        """
        
        sum_pair = 0.0
        segments = list(segments)
        for ind1 in range(len(segments)):
            for ind2 in range(ind1+1, len(segments)):
                sum_pair += hypot(segments[ind1].startx - segments[ind2].startx, segments[ind1].starty - segments[ind2].starty)
        return sum_pair



