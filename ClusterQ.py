"""
This example module shows various types of documentation available for use
with pydoc.  To generate HTML documentation for this module issue the
command:

    pydoc -w foo

"""
from Traclus_DL import *
from collections import defaultdict

class ClusterQ:
    """This is an implementation of a priority queue as needed for Traclus_DL.
    After running the DBScan with a particular segment, we will have a cluster of segments
    with a given sum of weights and a sum of squares of distances. If this cluster
    sum of weights reaches the minimum, this will be added to the queue.
    When it comes time to pop the queue, typically after all segments in the dataset have been considered,
    those with the highest sum of weights will be considered first. As a tie-breaker the sum of squares distances
    is considered, with those having the smallest sum of squares (eg "tighter" clusters being considered first)
    segments are being kept track of with the to_removed set to ensure that once they have been popped they are not considered again
    if a lower priority cluster is reached and found to contain segments already popped for a higher cluster, then the 
    cluster will either be removed altogether if it falls below the minimum weight sum threshold or re-added
    with a lower threshold if it is >= the minimum threshold"""


    def __init__(self, min_weight):


        self.entry_finder = {}               # mapping of seeds (segments) to entries
        self.REMOVED = ""     # placeholder for a removed task
        self.entry_hash = defaultdict(lambda : defaultdict(list))
        self.min_weight = min_weight
        self.priority_index = -1
        self.sumsq_list = []
        self.sumsq_index = -1
        self.index_range = []
        self.mindex = 0
        self.to_removed = set()

    def sum_pairwise(self, segments):
        """for a set of segments, returns the sum of distances for the set of all pairs of start points,
        when building corridors in a greedy fashion, the program sorts candidate corridors in decreasing order
        of the sum of their weights, and starts with the corridor having the highest weight. In cases of ties,
        "tighter" corridors (i.e. their constituent segments are closer together) given priority. This is the function used
        to determine the pairwise sum of squares of the member segments (note that weight is not considered)
        """

        sum_pair = 0.0
        segments = list(segments)
        for ind1 in range(len(segments)):
            for ind2 in range(ind1+1, len(segments)):
                sum_pair += hypot(segments[ind1].startx - segments[ind2].startx, segments[ind1].starty - segments[ind2].starty)
        return sum_pair


    def remove_cluster(self,cluster_seed):
        'Mark an existing cluster as REMOVED.  Raise KeyError if not found.'
        entry = self.entry_finder.pop(cluster_seed)
        entry[-1] = self.REMOVED


    def check_removed(self,cluster_seed, cluster):
        """check if any of the segments that make up a cluster have already been marked as removed (i.e. were part of an already popped cluster
        return True if yes (and remove the cluster if it falls below the weight, otherwise add the cluster again with a lower weight)
        and return False if none of the segments have been marked as removed"""
        removed = set()
        keeper = []
        sum_weight = 0.0
        for segment in cluster:
            if segment.id in self.to_removed:
                removed.add(segment)
            else:
                keeper.append(segment)
                sum_weight += segment.parent.weight
        
        if len(removed):
            if sum_weight < self.min_weight:
                self.remove_cluster(cluster_seed)
            else:
                self.add_cluster(cluster_seed, keeper, int(sum_weight*100))
            return True
        else:
            return False



    def add_cluster(self,cluster_seed, cluster, priority):
        'Add a new cluster or update the priority (sum of weights) of an existing cluster'
        sumsq = self.sum_pairwise(cluster)

        if cluster_seed in self.entry_finder:
            self.remove_cluster(cluster_seed)

        entry = [priority, sumsq, cluster_seed, cluster]
        self.entry_hash[priority][sumsq].append(entry)
        self.entry_finder[cluster_seed] = entry
        if priority >= self.priority_index:
            
            self.priority_index = priority + 1
            self.sumsq_index = 0
            self.seed_index = 0
            self.mindex = min(self.entry_hash.keys())
            self.sumsq_list = []


    def pop_cluster(self):
        """searches through queue for the highest priority, lowest sum of square cluster to return. if none found throws KeyError"""
        if not self.entry_hash:
            #nothing queued
            raise KeyError('pop from an empty priority queue')

        while True:

            while self.priority_index not in self.entry_hash and self.priority_index >= self.mindex:
                #decrease priority until find something that exists
                self.priority_index -= 1
                self.sumsq_index = 0;
                self.seed_index = 0;
                self.sumsq_list = []
                
            if len(self.sumsq_list ) < 1:
                #need to have a sorted list of all sum of squares corresponding to that weight, want to pop those with
                #a lower sum of square distance between member segments(i.e. denser clusters) first
                self.sumsq_list = sorted(self.entry_hash[self.priority_index])
 

            if self.seed_index >= len(self.entry_hash[self.priority_index][self.sumsq_list[self.sumsq_index]]):
                #we'e reached the end of clusters corresponnding to this particular priority and sum of square, need to more
                #to the next sum of square for that priority
                self.seed_index = 0
                self.sumsq_index += 1

            if self.sumsq_index >= len(self.sumsq_list):
                #we've done all the sum of squares for the given priority (i.e. all clusters for the priority have been popped,
                #time to decrease until we find one that still has sum of squares, or we reach the minimum in the queue.
                self.priority_index -= 1
                while self.priority_index not in self.entry_hash and self.priority_index >= self.mindex:
                    self.priority_index -= 1
                self.sumsq_index = 0
                self.seed_index = 0
                self.sumsq_list = sorted(self.entry_hash[self.priority_index])


                
            if self.priority_index < self.mindex: 
                #everything is popped!
                raise KeyError('pop from an empty priority queue')
            

       # print priority_index, sumsq_list, sumsq_index, seed_index
            priority, sumsq, cluster_seed, cluster = self.entry_hash[self.priority_index][self.sumsq_list[self.sumsq_index]][self.seed_index]
            self.seed_index = self.seed_index + 1
            if not self.check_removed(cluster_seed, cluster):
                #if something in this cluster has been marked as removed, it needs to decrease the priority and try again with a smaller version of it
                #if nothing has been marked as removed then can return it and mark its member segments as removed
                for segment in cluster:
                    self.to_removed.add(segment.id)
                return cluster, cluster_seed, priority
            


