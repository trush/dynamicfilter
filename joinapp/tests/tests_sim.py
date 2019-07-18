from __future__ import unicode_literals

from django.test import *
from joinapp.join_simulations import *
from joinapp.toggles import *
from plotting import *
from .. import graph_gen

def print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb):
        print "****************************** JOIN TYPE:", join_type, "******************************"
        if join_type in [2.1,2.2,3.1,3.2,3.3]:
            if have_sec_list is False:
                print "!!!!!!!!!!!!!!! INCORRECT SETTINGS, HAVE SEC LIST IS FALSE !!!!!!!!!!!!!!!"
        else:
            if have_sec_list is True:
                print "!!!!!!!!!!!!!!! INCORRECT SETTINGS, HAVE SEC LIST IS TRUE !!!!!!!!!!!!!!!"
        if num_prim != NUM_PRIM_ITEMS:
            print "****************************** NUMBER PRIMARY ITEMS:", num_prim
        if num_sec != NUM_SEC_ITEMS:
            print "****************************** NUMBER SECONDARY ITEMS:", num_sec
        if pjf_list != PJF_LIST:
            print "****************************** PJF LIST:", pjf_list
        if floor_fp != FLOOR_AMBIGUITY_FIND_PAIRS:
            print "****************************** CROWD FLOOR:", floor_fp
        if sec_pred_selectivity != SEC_PRED_SELECTIVITY:
            print "****************************** SEC PRED SELECTIVITY:", sec_pred_selectivity
        if join_cond_selectivity != JOIN_COND_SELECTIVITY:
            print "****************************** JOIN COND SELECTIVITY:", join_cond_selectivity
        if jf_amb != JF_AMBIGUITY:
            print "****************************** JOINABLE FILTER AMBIGUITY:", jf_amb
        if sec_pred_amb != SEC_PRED_AMBIGUITY:
            print "****************************** SECONDARY PREDICATE AMBIGUITY:", sec_pred_amb
        if join_cond_amb != JOIN_COND_AMBIGUITY:
            print "****************************** JOIN COND AMBIGUITY:", join_cond_amb
        if pjf_amb != PJF_AMBIGUITY:
            print "****************************** PJF AMBIGUITY:", pjf_amb

class Simulation_Tests(TestCase):
    # def test_multi_sim(self):
    #     sim = JoinSimulation()
    #     results = sim.run_multi_sims()

    def test_overnight_sim(self):
        # _____________________ STARTING TOGGLES _________________#
        num_prim = NUM_PRIM_ITEMS
        num_sec = NUM_SEC_ITEMS
        have_sec_list = HAVE_SEC_LIST
        pjf_list = PJF_LIST
        floor_fp = FLOOR_AMBIGUITY_FIND_PAIRS
        join_type = JOIN_TYPE
        ##########################
        sec_pred_selectivity = SEC_PRED_SELECTIVITY
        join_cond_selectivity = JOIN_COND_SELECTIVITY
        ###########################
        jf_amb = JF_AMBIGUITY
        sec_pred_amb = SEC_PRED_AMBIGUITY
        join_cond_amb = JOIN_COND_AMBIGUITY
        pjf_amb = PJF_AMBIGUITY
        print "this should just print the join type"
        print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        print "just join type printed? All good"


        
        #################### /UNEVEN DISTRIBUTION TRIALS
        prob_inf = 0.6 # likelihood an item will be influential
        inf_match = 0.8 # probability an influential item will match a given primary item even if it is not selected to match by the join predicate selectivity

        # # SIM 1
        # join_type = 1
        # have_sec_list = False
        # pjf_list = [("0", 1)]
        # join_cond_selectivity = 0.1
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
        # # SIM 2
        # join_type = 1.1
        # have_sec_list = False
        # join_cond_selectivity = 0.1
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
                        

        # prob_inf = 0.6 # likelihood an item will be influential
        # inf_match = 0.9 # probability an influential item will match a given primary item even if it is not selected to match by the join predicate selectivity

        # # SIM 1
        # join_type = 1
        # have_sec_list = False
        # pjf_list = [("0", 1)]
        # join_cond_selectivity = 0.1
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
        # # SIM 2
        # join_type = 1.1
        # have_sec_list = False
        # join_cond_selectivity = 0.1
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
                                 

        # prob_inf = 0.6 # likelihood an item will be influential
        # inf_match = 1 # probability an influential item will match a given primary item even if it is not selected to match by the join predicate selectivity

        # # SIM 1
        # join_type = 1
        # have_sec_list = False
        # pjf_list = [("0", 1)]
        # join_cond_selectivity = 0.1
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
        # # SIM 2
        # join_type = 1.1
        # have_sec_list = False
        # join_cond_selectivity = 0.1
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
                        


        inf_list = [0.9,1]
        match_list = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]


        for i in range(4):
            for inf in inf_list:
                for match_prob in match_list:
                    prob_inf = inf
                    inf_match = match_prob
                    print "--------------------------------------------------------------------"
                    print inf, match_prob
                    # SIM 1
                    join_type = 1
                    have_sec_list = False
                    pjf_list = [("0", 1)]
                    join_cond_selectivity = 0.1
                    print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
                    sim = JoinSimulation()
                    results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
                    # SIM 2
                    join_type = 1.1
                    have_sec_list = False
                    join_cond_selectivity = 0.1
                    print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
                    sim = JoinSimulation()
                    results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb, prob_inf, inf_match)
                    print inf, match_prob
                    print "--------------------------------------------------------------------"
        #################### /UNEVEN DISTRIBUTION TRIALS
        
        # # SIM 3
        # join_type = 1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # # SIM 4
        # join_type = 1.1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # # SIM 5
        # join_type = 1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # # SIM 5
        # join_type = 1.1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # # SIM 6
        # join_type = 1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # # SIM 7
        # join_type = 1.1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # # SIM 8
        # join_type = 1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # # SIM 9
        # join_type = 1.1
        # have_sec_list = False
        # print_dif(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)
        # sim = JoinSimulation()
        # results = sim.run_multi_overnight_sim(num_prim,num_sec,have_sec_list,pjf_list,floor_fp,join_type,sec_pred_selectivity,join_cond_selectivity, jf_amb, sec_pred_amb,join_cond_amb, pjf_amb)





   
    