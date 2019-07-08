from __future__ import unicode_literals

from django.test import *
from joinapp.join_simulations import *
from joinapp.toggles import *
from plotting import *
from .. import graph_gen

class Simulation_Tests(TestCase):
    # def test_sim(self):
    #     sim = JoinSimulation()
    #     sim.run_sim()
    # def test_multi_sim(self):
    #     sim = JoinSimulation()
    #     results = sim.run_multi_sims()
    #     #graph_gen.graph_time(results, "joinapp/simulation_files/testpjf_secpred_ambiguous.png")
    #     #sim.graph_multi_sim(results)
    #     #hist_gen(results[4], "joinapp/simulation_files/test2.png", labels = ('time','frequency'), title='Testing Itemwise Join', xRange=(None,None), yRange=(None,None), smoothness=True)
    #     #graph_gen.graph_prim_items_left(results, "joinapp/simulation_files/influential.png")

    def test_overnight_sim(self):
        print "*********************** Running First Simulation ***********************"
        print "JOIN TYPE:", toggles.JOIN_TYPE
        sim1 = JoinSimulation()
        results = sim1.run_multi_sims()
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "*********************** Finished First Simulation ***********************"


        print "*********************** Running Second Simulation ***********************"
        toggles.JOIN_TYPE = 3.3
        print "JOIN TYPE:", toggles.JOIN_TYPE
        sim2 = JoinSimulation()
        results = sim2.run_multi_sims()
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "*********************** Finished Second Simulation ***********************"

        print "*********************** Running Third Simulation ***********************"
        toggles.JOIN_TYPE = 3.2
        print "JOIN TYPE:", toggles.JOIN_TYPE
        sim3 = JoinSimulation()
        results = sim3.run_multi_sims()
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "*********************** Finished Third Simulation ***********************"