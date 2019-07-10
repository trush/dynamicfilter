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
    def test_multi_sim(self):
        sim = JoinSimulation()
        results = sim.run_multi_sims()
    #     #graph_gen.graph_time(results, "joinapp/simulation_files/testpjf_secpred_ambiguous.png")
    #     #sim.graph_multi_sim(results)
    #     #hist_gen(results[4], "joinapp/simulation_files/test2.png", labels = ('time','frequency'), title='Testing Itemwise Join', xRange=(None,None), yRange=(None,None), smoothness=True)
    #     #graph_gen.graph_prim_items_left(results, "joinapp/simulation_files/influential.png")


        
