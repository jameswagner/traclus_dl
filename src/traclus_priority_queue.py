from heapq import heappop, heappush
from math import hypot
from collections import defaultdict
from typing import Dict, List, Sequence, Set, Tuple, Optional, Any
from .trajectory import TrajectorySegment

class ClusterEntry:
    """
    Entry in the TraclusPriorityQueue representing a cluster of segments.
    
    Entries are prioritized by weight/density (higher is better) and 
    tightness (lower sum of distances is better).
    """
    
    def __init__(self, priority: float, cluster_seed: TrajectorySegment, 
                 cluster: Sequence[TrajectorySegment], removed: bool = False) -> None:
        """
        Initialize a cluster entry.
        
        Args:
            priority: Priority value (typically sum of weights)
            cluster_seed: The seed segment for this cluster
            cluster: All segments in this cluster
            removed: Whether this entry has been removed
        """
        self.priority: float = priority
        self.cluster_seed: TrajectorySegment = cluster_seed
        self.cluster: Sequence[TrajectorySegment] = cluster
        self.removed: bool = removed
    
    def __lt__(self, other: Any) -> bool:
        """
        Compare cluster entries for priority queue ordering.
        This is reversed (uses >) to ensure that the highest priority is popped first.
        
        Args:
            other: Another ClusterEntry to compare with
            
        Returns:
            True if this entry has higher priority than other
        """
        if not isinstance(other, ClusterEntry):
            return NotImplemented
        return self.priority > other.priority


class TraclusPriorityQueue:
    """
    Priority queue implementation for the Traclus_DL algorithm.
    
    After running the DBScan with a particular segment, we will have a cluster of segments
    with a given sum of weights and a sum of squares of distances. If this cluster
    sum of weights reaches the minimum, this will be added to the queue.
    
    When it comes time to pop the queue, typically after all segments in the dataset have been 
    considered, those with the highest sum of weights will be considered first. As a tie-breaker 
    the sum of squares distances is considered, with those having the smallest sum of squares 
    ("tighter" clusters) being considered first.
    
    Segments are tracked with the to_removed set to ensure that once they have been popped 
    they are not considered again. If a lower priority cluster is reached and found to contain 
    segments already popped for a higher cluster, then the cluster will either be removed
    altogether if it falls below the minimum weight sum threshold or re-added with a lower
    threshold if it is >= the minimum threshold.
    """

    def __init__(self, min_weight: float) -> None:
        """
        Initialize a priority queue.
        
        Args:
            min_weight: Minimum weight sum threshold for clusters
            
        Raises:
            ValueError: If min_weight is not positive
        """
        if min_weight <= 0:
            raise ValueError("Minimum weight must be positive")
            
        self.min_weight: float = min_weight
        self.pq: List[ClusterEntry] = []  # list of entries arranged in a heap
        self.entry_finder: Dict[TrajectorySegment, ClusterEntry] = {}  # mapping of segments to entries
        self.processed_segments: Set[TrajectorySegment] = set()
        
    def add_cluster(self, cluster_seed: TrajectorySegment, cluster: Sequence[TrajectorySegment], 
                   priority: float) -> None:
        """
        Add a new cluster or lazily remove any existing cluster with the same seed.
        
        Args:
            cluster_seed: Seed segment for the cluster
            cluster: Segments in the cluster
            priority: Priority value (typically sum of weights)
            
        Raises:
            ValueError: If the cluster is empty
        """
        if not cluster:
            raise ValueError("Cannot add an empty cluster")
            
        if cluster_seed in self.entry_finder:
            self.remove_cluster(cluster_seed)
            
        entry: ClusterEntry = ClusterEntry(priority, cluster_seed, cluster, False)
        self.entry_finder[cluster_seed] = entry
        heappush(self.pq, entry)
        
    def remove_cluster(self, cluster_seed: TrajectorySegment) -> None:
        """
        Lazily mark an existing cluster as removed.
        
        Args:
            cluster_seed: Seed segment for the cluster to remove
            
        Raises:
            KeyError: If the cluster with the given seed is not found
        """
        entry: ClusterEntry = self.entry_finder.pop(cluster_seed)
        entry.removed = True

    def pop_cluster(self) -> Sequence[TrajectorySegment]:
        """
        Remove and return the cluster with the highest priority.
        Ensures that segments already processed are not included in future clusters.
        
        Returns:
            A sequence of trajectory segments forming the cluster, or empty list if queue is empty
        """
        while self.pq:
            entry: ClusterEntry = heappop(self.pq)
            if not entry.removed:
                # Find segments that have already been processed in another cluster
                processed_segments: Sequence[TrajectorySegment] = [
                    seg for seg in entry.cluster if seg in self.processed_segments
                ]
                
                # If no segments have been processed, return the entire cluster
                if not processed_segments:
                    for segment in entry.cluster:
                        self.processed_segments.add(segment)
                    return entry.cluster
                
                # Otherwise, calculate the unprocessed segments and their weight
                unprocessed_segments: Sequence[TrajectorySegment] = [
                    seg for seg in entry.cluster if seg not in self.processed_segments
                ]
                unprocessed_weight: float = sum(
                    seg.weight for seg in unprocessed_segments
                )
                
                # If unprocessed weight is still above threshold, re-add to queue with updated priority
                if unprocessed_weight >= self.min_weight:
                    entry.cluster = unprocessed_segments
                    entry.priority = unprocessed_weight
                    heappush(self.pq, entry)
                # Otherwise, discard this cluster and continue to next
                
        return []

    def sum_pairwise(self, segments: Sequence[TrajectorySegment]) -> float:
        """
        Calculate the sum of distances for all pairs of segments.
        
        For a set of segments, returns the sum of distances for the set of all pairs of start 
        points. When building corridors in a greedy fashion, the program sorts candidate corridors 
        in decreasing order of the sum of their weights, and starts with the corridor having 
        the highest weight. In cases of ties, "tighter" corridors (i.e., their constituent 
        segments are closer together) are given priority.
        
        Args:
            segments: Sequence of trajectory segments
            
        Returns:
            Sum of pairwise distances between segment start points
        """
        if not segments:
            return 0.0
            
        sum_pair = 0.0
        segments_list = list(segments)
        
        for ind1 in range(len(segments_list)):
            for ind2 in range(ind1+1, len(segments_list)):
                sum_pair += hypot(
                    segments_list[ind1].start_x - segments_list[ind2].start_x, 
                    segments_list[ind1].start_y - segments_list[ind2].start_y
                )
                
        return sum_pair



