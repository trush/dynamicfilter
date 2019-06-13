from __future__ import unicode_literals

from django.test import *
from joinapp.join_simulations import *

class Simulation_Tests(TestCase):
    # def test_sim(self):
    #     sim = JoinSimulation()
    #     sim.run_sim()
    def test_multi_sim(self):
        sim = JoinSimulation()
        results = sim.run_multi_sims()
        sim.graph_multi_sim(results)
