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
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        sim1 = JoinSimulation()
        results = sim1.run_multi_sims()
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        print "*********************** Finished First Simulation ***********************"


        print "*********************** Running Second Simulation ***********************"
        toggles.JOIN_TYPE = 2
        toggles.SEC_PRED_AMBIGUITY = 0.7
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        sim2 = JoinSimulation()
        results = sim2.run_multi_sims()
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        print "*********************** Finished Second Simulation ***********************"

        print "*********************** Running Third Simulation ***********************"
        toggles.JOIN_TYPE = 2.1
        toggles.SEC_PRED_AMBIGUITY = 0.4
        toggles.HAVE_SEC_LIST = True
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        sim3 = JoinSimulation()
        results = sim3.run_multi_sims()
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        print "*********************** Finished Third Simulation ***********************"

        print "*********************** Running Fourth Simulation ***********************"
        toggles.JOIN_TYPE = 2.1
        toggles.SEC_PRED_AMBIGUITY = 0.7
        toggles.HAVE_SEC_LIST = True
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        sim3 = JoinSimulation()
        results = sim3.run_multi_sims()
        print "JOIN TYPE:", toggles.JOIN_TYPE
        print "SEC PRED AMBIGUITY", toggles.SEC_PRED_AMBIGUITY
        print "HAVE SEC LIST", toggles.HAVE_SEC_LIST
        print "*********************** Finished Fourth Simulation ***********************"