#NOTE: This can be ignored. It is an unfinished way of running different simulations with 
# the same synthetic ground truth information.




# def compare_dif_sims():
    #     random.seed()

    #     #__________________________ LOAD DATA __________________________ #
    #     estimator = Estimator.objects.create()
    #     jf_task_stats = TaskStats.objects.create(task_type=0)
    #     find_pairs_task_stats = TaskStats.objects.create(task_type=1)
    #     join_pairs_task_stats = TaskStats.objects.create(task_type=2)
    #     prejoin_task_stats = TaskStats.objects.create(task_type=3)
    #     sec_pred_task_stats = TaskStats.objects.create(task_type=4)


    #     syn_load_list() #load primary list for first simulation
    #     syn_load_pjfs(self.SecPJFTasks_Dict, self.PrimPJFTasks_Dict) #load pre-join filter ground truth
    #     syn_load_join_pairs_and_find_pairs(self.SecPJFTasks_Dict,self.PrimPJFTasks_Dict,self.FindPairsTasks_Dict,self.JoinPairTasks_Dict) #load join pairs and find pairs ground truth
    #     syn_load_sec_pred_tasks(self.SecPredTasks_Dict) #load secondary predicate ground truth

    #     simList = [0,1,2] #fill with type and order of simulations

    #     for current_sim in simList:
    #         if current_sim is 2 and HAVE_SEC_LIST is True:
    #             syn_load_second_list()

    #         self.generate_worker_ids()

    #         # list of assignments in progress, to be used in timed simulations
    #         active_assignments = {}
    #         #holds the keys for the assignments
    #         assignment_keys = {}
    #         key_counter = 0

    #         while(PrimaryItem.objects.filter(is_done=False).exists()):
    #             # pick worker
    #             worker_id = random.choice(self.worker_ids)

    #             self.num_prim_left += [PrimaryItem.objects.filter(is_done=False).count()]


    #             #__________________________  CHOOSE TASK __________________________#
    #             if current_sim is 0: # joinable filter
    #                 task = choose_task_JF(worker_id)
    #             elif current_sim is 1: # item-wise join
    #                 task = choose_task_IW(worker_id, estimator)
    #             elif current_sim is 2:
    #                 task = choose_task_PJF(worker_id, estimator)

        
    #             if type(task) is JFTask:
    #                 task_type = 0
    #                 my_item = task.primary_item.pk
    #                 hit = self.JFTasks_Dict[my_item]
    #             elif type(task) is FindPairsTask:
    #                 task_type = 1
    #                 my_item = task.primary_item.pk
    #                 hit = self.FindPairsTasks_Dict[my_item]
    #             elif type(task) is JoinPairTask:
    #                 task_type = 2
    #                 my_prim_item = task.primary_item.pk
    #                 my_sec_item = task.secondary_item.name
    #                 hit = self.JoinPairTasks_Dict[(my_prim_item, my_sec_item)]
    #             elif type(task) is PJFTask:
    #                 task_type = 3
    #                 if task.primary_item is not None:
    #                     my_item = task.primary_item.pk
    #                     hit = self.PrimPJFTasks_Dict[my_item]
    #                 else:
    #                     my_item = task.secondary_item.name
    #                     hit = self.SecPJFTasks_Dict[my_item]
    #             elif type(task) is SecPredTask:
    #                 task_type = 4
    #                 my_item = task.secondary_item.name
    #                 # Check for fake items
    #                 if REAL_DATA is False:
    #                     if int(my_item) >= NUM_SEC_ITEMS:
    #                         print "-----------------------A FAKE ITEM REACHED CONSENSUS-----------------------"
    #                 hit = self.SecPredTasks_Dict[my_item]

    #             #__________________________  ISSUE TASK __________________________#
    #             #choose a (matching) time and response for the task
    #             if task_type is not 2:
    #                 (prim,sec,time,answer) = hit
    #             else:
    #                 (pjf,time,answer) = hit
    #                 prim = my_prim_item
    #                 sec = my_sec_item

    #             if toggles.REAL_DATA:
    #                 ind = random.randint(0, len(times))
    #                 task_time = times[ind]
    #                 task_answer = responses[ind]
    #             else:
    #                 if task_type is 4:
    #                     task_answer,task_time = syn_answer_sec_pred_task(hit)
    #                 elif task_type is 3:
    #                     task_answer,task_time = syn_answer_pjf_task(hit)
    #                 elif task_type is 2:
    #                     task_answer,task_time = syn_answer_join_pair_task(hit)
    #                 elif task_type is 1:
    #                     task_answer,task_time = syn_answer_find_pairs_task(hit)
    #                 elif task_type is 0:
    #                     task_answer,task_time = syn_answer_joinable_filter_task(hit)

    #             if sec is not "None":
    #                 sec = SecondaryItem.objects.get(name=sec).pk
    #             else:
    #                 sec = None

                
    #             #__________________________ UPDATE STATE AFTER TASK __________________________ #
    #             if toggles.SIMULATE_TIME:
    #                 fin_list = []
    #                 for key in active_assignments:
    #                     active_assignments[key] -= toggles.TIME_STEP
    #                     if active_assignments[key] < 0:
    #                         fin_list.append(key)
    #                 assignment_keys[key_counter] = (task_type,task_answer,task_time,prim,sec)
    #                 active_assignments[key_counter] = task_time
    #                 key_counter += 1
    #                 for key in fin_list:
    #                     assignment = assignment_keys[key]
    #                     gather_task(assignment[0],assignment[1],assignment[2],assignment[3],assignment[4])
    #                     active_assignments.pop(key)
    #                     self.num_tasks_completed += 1
    #                     self.sim_time += task_time
    #             else:
    #                 gather_task(task_type,task_answer,task_time,prim,sec)
    #                 self.sim_time += task_time
    #                 self.num_tasks_completed += 1

    #             #update chao estimator
    #             estimator.refresh_from_db()
    #             estimator.chao_estimator()

    #         #simulate time cleanup loop, gets rid of ungathered tasks
    #         if toggles.SIMULATE_TIME:
    #             fin_list = []
    #             print active_assignments
    #             for key in active_assignments:
    #                 fin_list.append(key)
    #             for key in fin_list:
    #                 active_assignments.pop(key)
    #                 self.num_tasks_completed += 1
    #                 self.sim_time += task_time
        
    #     self.sim_time_arr += [self.sim_time]
    #     self.num_tasks_completed_arr += [self.num_tasks_completed]


    #     #__________________________ RESULTS __________________________#
    #     print "Finished simulation, printing results....."

    #     for item in PrimaryItem.objects.all():
    #         item.refresh_from_db()
        
    #     overlap_list = []
    #     for item in SecondaryItem.objects.all():
    #         item.refresh_from_db()
    #         overlap_list += [item.num_prim_items]
        
    #     i = max(overlap_list)
    #     while i >= 0:
    #         num_i_prims = SecondaryItem.objects.filter(num_prim_items = i).count()
    #         print "*", num_i_prims, "secondary item(s) were associated with", i, "primary items"
    #         i -= 1

    #     print ""
    #     print "Mean primary per secondary:", np.mean(overlap_list)
    #     print "Standard deviation primary per secondary:", np.std(overlap_list)
    #     print ""

    #     num_prim_pass = PrimaryItem.objects.filter(eval_result = True).count()
    #     num_prim_fail = PrimaryItem.objects.filter(eval_result = False).count()
    #     num_prim_missed = PrimaryItem.objects.filter(eval_result = None).count()
    #     join_selectivity = float(num_prim_pass)/float(PrimaryItem.objects.all().count())
    #     num_jf_tasks = JFTask.objects.all().count()
    #     num_find_pairs_tasks = FindPairsTask.objects.all().count()
    #     num_sec_pred_tasks = SecPredTask.objects.all().count()

    #     num_jf_assignments = 0
    #     for jftask in JFTask.objects.all():
    #         num_jf_assignments += jftask.num_tasks
    #     num_find_pairs_assignments = 0
    #     for fptask in FindPairsTask.objects.all():
    #         num_find_pairs_assignments += fptask.num_tasks
    #     num_sec_pred_assignments = 0
    #     for sptask in SecPredTask.objects.all():
    #         num_sec_pred_assignments += sptask.num_tasks



    #     print "*", num_prim_pass, "items passed the query"
    #     print "*", num_prim_fail, "items failed the query"
    #     print "* The simulation failed to evaluate", num_prim_missed, "primary items"
    #     print "* Query selectivity:", join_selectivity
    #     print "* Worker time spent:", self.sim_time[0]
    #     print "* Total number of tasks processed:", self.num_tasks_completed
    #     print "* # of joinable-filter tasks:", num_jf_tasks, "# of joinable-filter assignments:", num_jf_assignments
    #     print "* # of find pairs tasks:", num_find_pairs_tasks, "# of find pairs assignments:", num_find_pairs_assignments
    #     print "* # of secondary predicate tasks:", num_sec_pred_tasks, "# secondary predicate assignments:", num_sec_pred_assignments
    #     if REAL_DATA is True:
    #         self.accuracy_real_data() #does its own printing
    #     else:
    #         self.accuracy_syn_data() #does its own printing

    #     return (join_selectivity, num_jf_assignments, num_find_pairs_assignments, num_sec_pred_assignments, self.sim_time[0], self.num_tasks_completed)

