from __future__ import unicode_literals

from django.test import *
from joinapp.join_simulations import *
from plotting import *

class Simulation_Tests(TestCase):
    # def test_sim(self):
    #     sim = JoinSimulation()
    #     sim.run_sim()
    def test_multi_sim(self):
        sim = JoinSimulation()
        results = sim.run_multi_sims()
<<<<<<< HEAD
        #sim.graph_multi_sim(results)
        #hist_gen(results[4], "joinapp/simulation_files/test2.png", labels = ('time','frequency'), title='Testing Itemwise Join', xRange=(None,None), yRange=(None,None), smoothness=True)
=======
        hist_gen(results[4], "joinapp/simulation_files/test4.png", labels = ('time','frequency'), title='test 3 w/ 0 chance of none', xRange=(None,None), yRange=(None,None), smoothness=True)
>>>>>>> ed78c46946498fe156885b491f45e5806f646e7c
