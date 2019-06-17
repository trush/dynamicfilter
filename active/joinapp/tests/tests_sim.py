from __future__ import unicode_literals

from django.test import *
from joinapp.join_simulations import *
from plotting import *
from .. import graph_gen

class Simulation_Tests(TestCase):
    # def test_sim(self):
    #     sim = JoinSimulation()
    #     sim.run_sim()
    def test_multi_sim(self):
        sim = JoinSimulation()
        results = sim.run_multi_sims()
<<<<<<< HEAD
        #hist_gen(results[4], "joinapp/simulation_files/test4.png", labels = ('time','frequency'), title='test 3 w/ 0 chance of none', xRange=(None,None), yRange=(None,None), smoothness=True)
        # should do the same things as hist_gen above
        graph_gen.graph_time_vs_freq(results, "joinapp/simulation_files/test4_2.png")
=======
        #sim.graph_multi_sim(results)
        #hist_gen(results[4], "joinapp/simulation_files/test2.png", labels = ('time','frequency'), title='Testing Itemwise Join', xRange=(None,None), yRange=(None,None), smoothness=True)
>>>>>>> 25ccf979a57c00321ed265c6af43f55f6da055a4
