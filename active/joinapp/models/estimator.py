from items import *
from task_management_models import *

@python_2_unicode_compatible
class FStatistic(models.Model):
    """
    Model which keeps track of secondary items and the number of
    times that they are seen for the Estimator class.
    """
    # number of times that items are seen in the sample
    num_in_sample = models.IntegerField(default=0)
    # number of items seen num_in_sample times in the sample, maybe we don't need this
    num_of_items = models.IntegerField(default=0)
    # relations to keep track of which items are seen num_in_sample times
    items = models.ManyToManyField(SecondaryItem, related_name="f_statistic")

@python_2_unicode_compatible
class Estimator(models.Model):
    """
    Model to keep track of the completeness of the second list.
    Stores variables needed in the chao_estimator() function.
    """
    has_2nd_list = models.BooleanField(default=None)
    
    # Enumeration Vars #

    ## @remarks Used in the enumeration estimate in chao_estimator()
    total_sample_size = models.IntegerField(default=0)
    f_statistics = models.ManyToManyField(FStatistic, related_name='estimator')

    def __str__(self):
        return "Estimator for Species Enumeration"

    def update_chao_estimator_variables(self, join_pair_task):

        # both variables updated in PW join in join class in section shown below
        if not self.has_2nd_list:
            if self.f_statistics.count() is 0:
                self.f_statistics.create(num_in_sample=1,num_of_items=1,items.add(join_pair_task.secondary_item))
            else:
                been_added = False
                entry = 1 # known first key
                # try to add it to correct FStatistic
                while not been_added:
                    for f_stat in self.f_statistics.filter(num_in_sample=1): # there should only be one of these f_stats
                        if join_pair_task.secondary_item in f_stat.items:
                            f_stat.items.remove(join_pair_task.secondary_item)
                            f_stat.num_of_items -= 1
                            if self.f_statistics.filter(num_in_sample=entry+1).count() is not 0:
                                for f_stat in self.f_statistics.filter(num_in_sample=entry+1):
                                    f_stat.items.add(join_pair_task.secondary_item)
                                    f_stat.num_of_items += 1
                                    been_added = True
                            else:
                                self.f_statistics.create(num_in_sample=entry+1,num_of_items=1,items.add(join_pair_task.secondary_item))
                                been_added = True
                        entry += 1
                        if self.f_statistics.filter(num_in_sample=entry).count() is 0:
                            break
                if not been_added:
                    for f_stat in self.f_statistics.filter(num_in_sample=1): # there should only be one of these f_stats
                        f_stat.items.add(join_pair_task.secondary_item)
                        f_stat.num_of_items += 1
        self.total_sample_size += 1
    


    ## @param self
    # @return true if the current size of the list is within a certain threshold of the total size of the list (according to the chao estimator)
    #   and false otherwise.
    # @remarks Uses the Chao92 equation to estimate population size during enumeration.
    #	To understand the math computed in this function see: http://www.cs.albany.edu/~jhh/courses/readings/trushkowsky.icde13.enumeration.pdf 
    def chao_estimator(self):
        # prepping variables
        if self.total_sample_size <= 0:
            return False
        for f_stat in self.f_statistics.filter(num_in_sample=1):
            count = f_stat.num_of_items
        c_hat = 1-float(count)/self.total_sample_size
        sum_fis = 0
        for f_stat in self.f_statistics:
            n = f_stat.num_in_sample
            sum_fis += n*(n-1)*f_stat.num_of_items
        num_sec_items = SecondaryItem.objects.count()
        gamma_2 = max((num_sec_items/c_hat*sum_fis)/\
                    (self.total_sample_size*(self.total_sample_size-1)) -1, 0)
        # final equation
        N_chao = num_sec_items/c_hat + self.total_sample_size*(1-c_hat)/(c_hat)*gamma_2
        # if we are comfortably within a small margin of the total set, we call it close enough
        if N_chao > 0 and abs(N_chao - num_sec_items) < toggles.THRESHOLD * N_chao:
            return True
        return False