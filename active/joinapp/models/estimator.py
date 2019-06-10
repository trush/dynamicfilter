from items import *
from task_management_models import *

@python_2_unicode_compatible
class FStatistic(models.Model):
    """
    Model which keeps track of secondary items and the number of
    times that they are seen for the Estimator class.
    """
    # number of times that items are seen in the sample
    times_seen = models.IntegerField(default=0)
    # number of items seen times_seen times in the sample, maybe we don't need this
    num_of_items = models.IntegerField(default=0)
    # relations to keep track of which items are seen times_seen times
    estimator = models.ForeignKey('Estimator')

    def __str__(self):
        return "FStats for " + str(self.times_seen) + " with" + str(self.num_of_items) + "items."

@python_2_unicode_compatible
class Estimator(models.Model):
    """
    Model to keep track of the completeness of the second list.
    Stores variables needed in the chao_estimator() function.
    """
    has_2nd_list = models.BooleanField(default=False)
    
    # Enumeration Vars #

    ## @remarks Used in the enumeration estimate in chao_estimator()
    total_sample_size = models.IntegerField(default=0)

    def __str__(self):
        return "Estimator for Species Enumeration"

    def update_chao_estimator_variables(self, join_pair_task):

        if not FStatistic.objects.all().exists():
            new_fstat = FStatistic.objects.create(times_seen=1,num_of_items=1,estimator=self)

            sec_item = join_pair_task.secondary_item
            sec_item.fstatistic = new_fstat
            sec_item.save()
            
        else:
            sec_item = join_pair_task.secondary_item
            f_stat = sec_item.fstatistic

            if f_stat == None:
                f_stat1 = FStatistic.objects.get(times_seen=1, estimator=self)
                sec_item.fstatistic = f_stat1
                f_stat1.num_of_items += 1

                f_stat1.save()
                sec_item.save()

            else:             
                times_seen_updated = f_stat.times_seen + 1
                f_stat_n = None
                if FStatistic.objects.filter(times_seen=times_seen_updated, estimator=self).exists():
                    f_stat_n = FStatistic.objects.get(times_seen=times_seen_updated, estimator=self)         
                else:
                    f_stat_n = FStatistic.objects.create(times_seen=times_seen_updated, num_of_items=0, estimator=self)
                f_stat_n.num_of_items += 1
                f_stat.num_of_items -= 1

                sec_item.fstatistic = f_stat_n

                f_stat_n.save()
                f_stat.save()
                sec_item.save()

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
        f_stat = FStatistic.objects.get(times_seen=1)
        count = f_stat.num_of_items

        c_hat = 1-float(count)/self.total_sample_size
        sum_fis = 0

        for f_stat in FStatistic.objects.filter(estimator = self):
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