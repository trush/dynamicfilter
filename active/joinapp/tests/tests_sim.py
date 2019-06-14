from __future__ import unicode_literals

from django.test import *
from joinapp.join_simulations import *
from joinapp.simulation_files.plotScript import *

class Simulation_Tests(TestCase):
    # def test_sim(self):
    #     sim = JoinSimulation()
    #     sim.run_sim()
    def test_multi_sim(self):
        sim = JoinSimulation()
        results = sim.run_multi_sims()
        hist_gen(results[4], "joinapp/simulation_files/test1.png", labels = ('time','frequency'), title='Testiing Itemwise Join', xRange=(None,None), yRange=(None,None), smoothness=True)