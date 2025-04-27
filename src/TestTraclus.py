import unittest
from collections import defaultdict
from Trajectory import *
from Traclus_DL import *
from math import *

class TestTraclus(unittest.TestCase):

    def setUp(self):
        self.infile = "testlines.txt";        
        self.max_dist =  100.0
        self.max_angle = 10.0
        self.min_weight = 1.0
        self.segment_size = 10.0
        self.traj_angles = defaultdict(list) #look up angles fast, each angle (in degrees) will have a list of Trajectory objects
        self.trajectories = [] # list of trajectories, keep it?
        read_file(infile=self.infile, segment_size=self.segment_size, traj_angles=self.traj_angles, trajectories=self.trajectories)
        self.segment_to_line_dist =  defaultdict(lambda : defaultdict(float))
        self.segment_to_line_closest_seg =  defaultdict(lambda : defaultdict(Trajectory.TrajectorySegment))
        


    def test_segmentation(self):
        
        #horizontal line:
        hor = Trajectory(startx=200,starty=300.0,endx=300.0,endy=300.0)
        self.assertEqual(hor.angle, 0)

        neg_hor = Trajectory(startx=200,starty=300.0,endx=100.0,endy=300.0)
        self.assertEqual(abs(neg_hor.angle), 180)

        ver = Trajectory(startx=200,starty=300.0,endx=200.0,endy=400.0)
        self.assertEqual(ver.angle, 90)

        neg_ver = Trajectory(startx=200,starty=300.0,endx=200.0,endy=200.0)
        self.assertEqual(neg_ver.angle, -90)

        ang20 = Trajectory(startx=200,starty=300,endx=293.969262092233, endy = 334.202014295086)
        self.assertAlmostEqual(ang20.angle,20, 7)


        ang_minus20 = Trajectory(startx=200,starty=300,endx=293.969262092233, endy = 265.797985704914)
        self.assertAlmostEqual(ang_minus20.angle,-20, 7)


        


        hor.make_segments(segment_length=12)
        neg_hor.make_segments(segment_length=12)
        ver.make_segments(segment_length=12)
        neg_ver.make_segments(segment_length=12)
        ang20.make_segments(segment_length=12)
        ang_minus20.make_segments(segment_length=12)

        self.assertEqual(len(hor.segments),9)
        self.assertEqual(len(neg_hor.segments),9)

        self.assertEqual(len(ver.segments),9)
        self.assertEqual(len(neg_ver.segments),9)

        self.assertEqual(len(ang20.segments),9)
        self.assertEqual(len(ang_minus20.segments),9)



        for i in range(9):
            self.assertAlmostEqual(hor.segments[i].startx, 200+cos(radians(0))*i*12.)
            self.assertAlmostEqual(hor.segments[i].starty, 300+sin(radians(0))*i*12.)

            self.assertAlmostEqual(neg_hor.segments[i].startx, 200+cos(radians(180))*i*12.)
            self.assertAlmostEqual(neg_hor.segments[i].starty, 300+sin(radians(180))*i*12.)

            self.assertAlmostEqual(ver.segments[i].startx, 200+cos(radians(90))*i*12.)
            self.assertAlmostEqual(ver.segments[i].starty, 300+sin(radians(90))*i*12.)

            self.assertAlmostEqual(neg_ver.segments[i].startx, 200+cos(radians(-90))*i*12.)
            self.assertAlmostEqual(neg_ver.segments[i].starty, 300+sin(radians(-90))*i*12.)

            self.assertAlmostEqual(ang20.segments[i].startx, 200+cos(radians(20))*i*12.)
            self.assertAlmostEqual(ang20.segments[i].starty, 300+sin(radians(20))*i*12.)

            self.assertAlmostEqual(ang_minus20.segments[i].startx, 200+cos(radians(-20))*i*12.)
            self.assertAlmostEqual(ang_minus20.segments[i].starty, 300+sin(radians(-20))*i*12.)









    def test_DBScan(self):
        # make sure the shuffled sequence does not lose any elements
        #traj =  get_traj_by_name(trajectories=self.trajectories, name="par_ver1")
        #print traj
        expected = {
            'par_ver1':7.03, 
            'par_ver2':7.03, 
            'par_ver3':7.03, 
            'par_hor1':7.06, 
            'par_hor2':7.06,
            'par_hor3':7.06,
            'par_diag1':7.09,
            'par_diag2':7.09,
            'par_diag3':7.09,
            'par_neg_diag1':7.12,
            'par_neg_diag1':7.12,
            'par_neg_diag1':7.12,
            'par_expand1':7.15,
            'par_expand2':7.15,
            'par_expand3':7.15,
            'angle_test1_90':3.16,
            'angle_test2_95':7.24,
            'angle_test3_102':6.16,
            'no_clust1':1.21,
            'no_clust2':1.22,
            'no_clust3':1.23,
            'long_exp1':63.66,
            'long_exp2':63.66,
            'long_exp3':63.66,
            'long_exp4':63.66,
            'long_exp5':63.66,
            'long_exp6':63.66,
            'no_expand0':-1,
            'no_expand1':1.1,
            'no_expand2':-1,
            'no_expand3':-1,
            'no_expand4':-1,
            'no_expand5':-1,
            'expand_fixed0':-1,
            'expand_fixed1':1.501,
            'expand_fixed2':1.501,
            'expand_fixed3':-1,
            'expand_fixed4':-1,
            'expand_fixed5':-1,
            'expand_fixed6':-1
            }
        for traj in self.trajectories:
            for seg in traj.segments:
                if traj.name in expected:
                    sum_weight, segments = DBScan(seg, self.traj_angles,  self.max_dist, self.min_weight, self.max_angle, self.segment_to_line_dist, self.segment_to_line_closest_seg)        
                    self.assertAlmostEqual(sum_weight, expected[traj.name]);
#                    print sum_weight
        #three parallel vertical lines, less than max_dist

        #three parallel horizontal lines, less than max_dist

        #three parallel diagonol lines, less than max_dist
        
        #line b is less than max distance from the seed, another line is less than max distance from line b. All three should be obtained

        #line a and b have angle less than max angle and distance less than max distance, line c has less than max dist from line b 
        #however it is more than max angle from a therefore the expansion does NOT continue to line c.

        #line c is shorter than a and b, therefore the continuation after the end of c should have lower weight. 



        #lines have angle 0 and sum to more than the minimum, however they are more than max distance, so no cluster




    def test_queue(self):

        Q = build_DB_queue(self.trajectories, self.traj_angles,  self.max_dist, self.min_weight, self.max_angle, self.segment_to_line_dist, self.segment_to_line_closest_seg)       
        clus_count = 0;
        while True:
            try:
                cluster, cluster_seed, priority = Q.pop_cluster()
                if clus_count < 11:
                    self.assertAlmostEqual(priority/100, 10000) #cluster1 in file
                elif clus_count < 22:
                    self.assertAlmostEqual(priority/100, 2000)
                    self.assertMultiLineEqual(cluster_seed.parent.name, "cluster2_1")
                elif clus_count < 33:
                    self.assertAlmostEqual(priority/100, 2000)
                    self.assertMultiLineEqual(cluster_seed.parent.name, "cluster3_1")
                elif clus_count < 44:
                    self.assertAlmostEqual(priority/100, 500) #greedy1_2 to greedy1_6 in file
                elif clus_count < 66:
                    self.assertAlmostEqual(priority/100, 99) #greedy1_1 and greedy1_7 in file
                clus_count += 1
            except KeyError:
                break





if __name__ == '__main__':
    unittest.main()
