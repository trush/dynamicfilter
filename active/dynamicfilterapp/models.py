from django.db import models
from django.core.validators import RegexValidator
from validator import validate_positive
import subprocess
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.postgres.fields import ArrayField
from scipy.special import btdtr
import toggles
import math

@python_2_unicode_compatible
class Item(models.Model):
    """
    General model representing an item in the database
    """
    item_ID = models.IntegerField(default=None)
    name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=50)
    address = models.CharField(max_length=200, default='')

    # set to True if one of the predicates has been evaluated to False
    hasFailed = models.BooleanField(db_index=True, default=False)
    shouldPass = models.BooleanField(db_index = True, default=False)

    # attributes for item specific systems
    isStarted = models.BooleanField(default=False)
    almostFalse = models.BooleanField(default=False)

    inQueue = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)

    def add_to_queue(self):
        self.inQueue = True
        self.save(update_fields=["inQueue"])

    def remove_from_queue(self):
        self.inQueue = False
        self.save(update_fields=["inQueue"])

    def reset(self):
        self.hasFailed=False
        self.isStarted=False
        self.almostFalse=False
        self.inQueue=False
        self.save(update_fields=["hasFailed","isStarted","almostFalse","inQueue"])


@python_2_unicode_compatible
class Question(models.Model):
    """
    Model for questions in the database
    """
    question_ID = models.IntegerField(default=None)
    question_text = models.CharField(max_length=200)
    def __str__(self):
        return self.question_text

class WorkerID(models.Model):
    """
    Restricts worker ID to positive integers. Used in IDForm in forms.py.
    (may want to change this to a string for future use)
    """
    workerID = models.IntegerField(validators=[validate_positive], unique=True, db_index=True)

@python_2_unicode_compatible
class Predicate(models.Model):
    """
    Model representing one predicate
    """
    predicate_ID = models.IntegerField(default=None)
    question = models.ForeignKey(Question)

    # lottery system variables
    num_tickets = models.IntegerField(default=1)
    num_wickets = models.IntegerField(default=0)

    def _get_num_pending(self):
        return IP_Pair.objects.filter(inQueue=True, predicate=self).count()

    num_pending = property(_get_num_pending)

    # Queue variables
    queue_is_full = models.BooleanField(default=False)
    queue_length = models.IntegerField(default=toggles.PENDING_QUEUE_SIZE)

    # Consensus variables
    _consensus_max = models.IntegerField(default=toggles.CUT_OFF)   # the max number of votes to ask for
    _consensus_status = models.IntegerField(default=0)              # used in adaptive consensus for bookeeping
    _consensus_uncertainty_threshold = models.FloatField(default=toggles.UNCERTAINTY_THRESHOLD) # used for bayes stuff (see toggles)
    _consensus_decision_threshold   = models.FloatField(default=toggles.DECISION_THRESHOLD)     # used for bayes stuff (see toggles)

    @property
    def consensus_max(self):
        if not toggles.PREDICATE_SPECIFIC:
            return toggles.CUT_OFF
        return self._consensus_max

    @consensus_max.setter
    def consensus_max(self,value):
        if not toggles.PREDICATE_SPECIFIC:
            toggles.CUT_OFF = value
        else:
            self._consensus_max=value
            self.save(update_fields=['_consensus_max'])

    @property
    def consensus_max_single(self):
        return int(1+math.ceil(self.consensus_max/2.0))

    @property
    def consensus_status(self):
        if not toggles.PREDICATE_SPECIFIC:
            return toggles.CONSENSUS_STATUS
        return self._consensus_status

    @consensus_status.setter
    def consensus_status(self,value):
        if not toggles.PREDICATE_SPECIFIC:
            toggles.CONSENSUS_STATUS = value
        else:
            self._consensus_status = value
            self.save(update_fields=["_consensus_status"])

    @property
    def consensus_uncertainty_threshold(self):
        if not toggles.PREDICATE_SPECIFIC:
            return toggles.UNCERTAINTY_THRESHOLD
        return self._consensus_uncertainty_threshold

    @property
    def consensus_decision_threshold(self):
        if not toggles.PREDICATE_SPECIFIC:
            return toggles.DECISION_THRESHOLD
        return self._consensus_decision_threshold

    # fields to keep track of selectivity
    selectivity = models.FloatField(default=0.1)
    calculatedSelectivity = models.FloatField(default=0.1)
    trueSelectivity = models.FloatField(default=0.0)
    trueAmbiguity = models.FloatField(default=0.0)
    totalTasks = models.FloatField(default=0.0)
    totalNo = models.FloatField(default=0.0)
    num_ip_complete = models.IntegerField(default=0)

    # fields to keep track of cost
    cost = models.FloatField(default=0.0)
    avg_completion_time = models.FloatField(default=0.0)
    avg_tasks_per_pair = models.FloatField(default=0.0)

    def __str__(self):
        return "Predicate branch with question: " + self.question.question_text

    def updateSelectivity(self):
        self.calculatedSelectivity = self.totalNo/self.totalTasks
        return self.calculatedSelectivity

    def setTrueSelectivity(self, sel):
        self.trueSelectivity = sel
        self.save(update_fields=["trueSelectivity"])

    def setTrueAmbiguity(self, amb):
        self.trueAmbiguity = amb
        self.save(update_fields=["trueAmbiguity"])

    def update_cost(self):
        self.cost = self.avg_completion_time * self.avg_tasks_per_pair
        return self.cost

    def move_window(self):
        if self.num_wickets == toggles.LIFETIME:
            self.num_wickets = 0
            self.save(update_fields=["num_wickets"])

            if self.num_tickets > 1:
                self.num_tickets -= 1
                self.save(update_fields=["num_tickets"])

    def award_ticket(self):
        self.num_tickets += 1
        self.save(update_fields = ["num_tickets"])

    def award_wicket(self):
        self.num_wickets += 1
        self.save(update_fields=["num_wickets"])

    def add_no(self):
        self.totalNo += 1
        self.save(update_fields=["totalNo"])

    def check_queue_full(self):
        if self.num_pending == self.queue_length:
            self.queue_is_full = True
            self.save(update_fields = ["queue_is_full"])
        elif self.num_pending < self.queue_length:
            self.queue_is_full = False
            self.save(update_fields = ["queue_is_full"])
        else:
            raise Exception ("Queue for predicate " + str(self.id) + " is over-full")

        if IP_Pair.objects.filter(inQueue=True, predicate = self).count() < self.queue_length and self.queue_is_full:
            raise Exception ("Queue for predicate " + str(self.id) + " set to full when not")

    def remove_ticket(self):
        self.num_tickets -= 1
        self.save(update_fields=["num_tickets"])

    def add_total_task(self):
        self.totalTasks += 1
        self.save(update_fields=["totalTasks"])

    def inc_queue_length(self):
        self.queue_length += 1
        self.queue_is_full = False
        self.save(update_fields=["queue_length", "queue_is_full"])

        return self.queue_length

    def dec_queue_length(self):
        """
        decreases the queue_length value of the given predicate by one
        raises an error if the pred was full when called
        """
        if (self.queue_is_full):
            raise ValueError("Tried to decrement the queue_length of a predicate with a full queue")
        old = self.queue_length
        if old == 1:
            raise ValueError("Tried to decrement queue_length to zero")
        self.queue_length = old-1
        self.save(update_fields=["queue_length"])
        if self.num_pending >= (old - 1):
            self.queue_is_full = True
            self.save(update_fields=["queue_is_full"])

        return self.queue_length

    def adapt_queue_length(self):
        '''
        depending on adaptive queue mode, changes queue length as appropriate
        '''
        self.refresh_from_db()
        # print "adapt queue length called"
        if toggles.ADAPTIVE_QUEUE_MODE == 0:
            # print "increase version invoked"
            for pair in toggles.QUEUE_LENGTH_ARRAY:
                if self.num_tickets > pair[0] and self.queue_length < pair[1]:
                    self.inc_queue_length()
                    break
            return self.queue_length

        if toggles.ADAPTIVE_QUEUE_MODE == 1:
            for pair in toggles.QUEUE_LENGTH_ARRAY:
                if self.num_tickets > pair[0] and self.queue_length < pair[1]:
                    self.inc_queue_length()
                    break
                elif self.num_tickets <= pair[0] and self.queue_length >= pair[1]:
                    self.dec_queue_length()
                    break
            return self.queue_length

    ### Adaptive Consensus Methods
    def _should_change_size(self):
        lower_bound, upper_bound = toggles.CONSENSUS_STATUS_LIMITS
        if self.consensus_status >= upper_bound:
            if self.consensus_max < toggles.CONSENSUS_SIZE_LIMITS[1]:
                return 1
            return 2
        elif self.consensus_status <= lower_bound:
            if self.consensus_max > toggles.CONSENSUS_SIZE_LIMITS[0]:
                return -1
            return -2
        else:
            return False

    def _change_size(self, d):
        #TODO change hardcoded 2 to a toggleable?
        if d == 1:
            self.consensus_max = self.consensus_max + 2
        elif d == -1:
            self.consensus_max = self.consensus_max - 2
        self.consensus_status = 0
        if d == 2:
            self.consensus_status = 1
        elif d == -2:
            self.consensus_status = -1
        print "Size: "+str(self.consensus_max)

    def _update_status(self, ipPair):
        #TODO find way to modularize this
        if ipPair.consensus_location == 1:
            self.consensus_status = self.consensus_status - 1
        elif ipPair.consensus_location == 2:
            if self.consensus_status < 0:
                self.consensus_status = 0
        elif ipPair.consensus_location == 3:
            self.consensus_status = self.consensus_status + 1
        elif ipPair.consensus_location == 4:
            self.consensus_status = self.consensus_status + 3
        print "Status: "+str(self.consensus_status)


    def update_consensus(self, ipPair):
        mode = 2
        old_max = self.consensus_max
        new_max = old_max

        ### TESTING RENO slow start method
        if mode == 1:
            loc = ipPair.consensus_location
            if loc == 1:
                self.consensus_status = self.consensus_status + 1
            elif loc == 3:
                self.consensus_status = self.consensus_status/2
            elif loc == 4:
                self.consensus_status = self.consensus_status/3
            new_max = toggles.CONSENSUS_SIZE_LIMITS[1] - (self.consensus_status*2)
            if new_max < toggles.CONSENSUS_SIZE_LIMITS[0]:
                new_max=toggles.CONSENSUS_SIZE_LIMITS[0]
            print "Size: "+str(new_max)
            self.consensus_max = new_max

        ### CUTE alg. method.
        elif mode == 2:
            loc = ipPair.consensus_location
            if loc == 1:
                self.consensus_status = self.consensus_status + 1
            elif (loc == 3) or (loc == 4):
                self.consensus_status = 0
            new_max = toggles.CONSENSUS_SIZE_LIMITS[1] - (self.consensus_status*2)
            if new_max < toggles.CONSENSUS_SIZE_LIMITS[0]:
                new_max = toggles.CONSENSUS_SIZE_LIMITS[0]
            print "Size: "+str(new_max)
            self.consensus_max = new_max

        ## WEIRD AF mode
        elif mode == 0:
            self._update_status(ipPair)
            # update status
            status = self._should_change_size()
            if status:
                self._change_size(status)

        if new_max>old_max:
            return True
        return False

    def reset(self):
        self.num_tickets=1
        self.num_wickets=0
        self.num_ip_complete=0
        self.selectivity=0.1
        self.totalTasks=0
        self.totalNo=0
        self.queue_is_full=False
        self.queue_length=toggles.PENDING_QUEUE_SIZE
        self.consensus_status=0
        self.consensus_max=toggles.CUT_OFF
        self.save(update_fields=["num_tickets","num_wickets","num_ip_complete","selectivity","totalTasks","totalNo","queue_is_full","queue_length"])


@python_2_unicode_compatible
class IP_Pair(models.Model):
    """
    Model representing an item-predicate pair.
    """
    item = models.ForeignKey(Item)
    predicate = models.ForeignKey(Predicate)

    # tasks issued
    tasks_out = models.IntegerField(default=0)
    # running cumulation of votes
    value = models.FloatField(default=0.0)
    num_no = models.IntegerField(default=0)
    num_yes = models.IntegerField(default=0)
    isDone = models.BooleanField(db_index=True, default=False)

    # a marker for the status of the IP
    status_votes = models.IntegerField(default=0)

    inQueue = models.BooleanField(default=False, db_index=True)

    # for random algorithm
    isStarted = models.BooleanField(default=False)

    def __str__(self):
        return self.item.name + "/" + self.predicate.question.question_text

    def _get_should_leave_queue(self):
        return self.isDone and self.tasks_out < 1

    should_leave_queue = property(_get_should_leave_queue)

    def is_false(self):
        if self.isDone and (self.value < 0):
            self.item.hasFailed = True
            self.item.save(update_fields=["hasFailed"])
        return self.item.hasFailed

    def _get_is_in_queue(self):
        return self.inQueue

    is_in_queue = property(_get_is_in_queue)

    def add_to_queue(self):
        self.inQueue = True
        self.save(update_fields=["inQueue"])
        if IP_Pair.objects.filter(inQueue=True, predicate=self.predicate).count() > self.predicate.queue_length:
            raise Exception ("Too many IP pair objects in queue for predicate " + str(self.predicate.id))
        self.item.add_to_queue()
        self.predicate.award_ticket()
        if not IP_Pair.objects.filter(predicate=self.predicate, inQueue=True).count() == self.predicate.num_pending:
            print "IP objects in queue for pred " + str(self.predicate.id) + ": " + str(IP_Pair.objects.filter(predicate=self.predicate, inQueue=True).count())
            print "Number pending for pred " + str(self.predicate.id) + ": " + str(self.predicate.num_pending)
            raise Exception("ADD_TO_QUEUE Mismatch num_pending and number of IPs in queue for pred " + str(p.id))
        # checks if pred queue is now full and changes state accordingly
        self.predicate.check_queue_full()

    def remove_from_queue(self):
        if self.should_leave_queue :
            self.inQueue = False
            self.save(update_fields=["inQueue"])
            self.item.remove_from_queue()
            self.predicate.check_queue_full()

    def record_vote(self, workerTask):
        # add vote to tally only if appropriate
        if not self.isDone:
            self.status_votes += 1
            self.predicate.award_wicket()
            self.save(update_fields=["status_votes"])

            if workerTask.answer:
                self.value += 1
                self.num_yes += 1
                self.save(update_fields=["value", "num_yes"])

            elif not workerTask.answer:
                self.value -= 1
                self.num_no += 1
                self.predicate.add_no()
                self.save(update_fields=["value", "num_no"])

            self.predicate.updateSelectivity()
            self.predicate.update_cost()
            # TODO @ Mahlet add your update rank and stuff here!

            self.set_done_if_done()

    def set_done_if_done(self):

        if self.status_votes == toggles.NUM_CERTAIN_VOTES:

            if self.found_consensus():
                self.isDone = True
                self.save(update_fields=["isDone"])
                if toggles.ADAPTIVE_CONSENSUS:
                    self.predicate.update_consensus(self)

                if not self.is_false() and self.predicate.num_tickets > 1:
                    self.predicate.remove_ticket()

                if self.is_false():
                    IP_Pair.objects.filter(item__hasFailed=True).update(isDone=True)

                # helpful print statements
                if toggles.DEBUG_FLAG:
                    print "*"*96
                    print "Completed IP Pair: " + str(self.id)
                    print "Total votes: " + str(self.num_yes+self.num_no) + " | Total yes: " + str(self.num_yes) + " |  Total no: " + str(self.num_no)
                    print "Total votes: " + str(self.num_yes+self.num_no)
                    print "There are now " + str(IP_Pair.objects.filter(isDone=False).count()) + " incomplete IP pairs"
                    print "*"*96

            else:
                self.status_votes -= 2
                self.save(update_fields=["status_votes"])

    def _consensus_finder(self):
        """
        key:
            0 - no consensus
            1 - unAmbigous Zone
            2 - medium ambiguity Zone
            3 - high ambiguity zone
            4 - most ambiguity
        """
        myPred = self.predicate
        votes_cast = self.num_yes + self.num_no
        larger = max(self.num_yes, self.num_no)
        smaller = min(self.num_yes, self.num_no)

        uncertLevel = 2
        if toggles.BAYES_ENABLED:
            if self.value > 0:
                uncertLevel = btdtr(self.num_yes+1, self.num_no+1, myPred.consensus_decision_threshold)
            else:
                uncertLevel = btdtr(self.num_no+1, self.num_yes+1, myPred.consensus_decision_threshold)


        if votes_cast >= myPred.consensus_max:
            return 4

        elif uncertLevel < myPred.consensus_uncertainty_threshold:
            return 1

        elif larger >= myPred.consensus_max_single:
            if smaller < myPred.consensus_max_single*(1.0/3.0):
                return 1
            elif smaller < myPred.consensus_max_single*(2.0/3.0):
                return 2
            else:
                return 3

        else:
            return 0

    def found_consensus(self):
        if not toggles.ADAPTIVE_CONSENSUS:
            return bool(self._consensus_finder())
        if not bool(self._consensus_finder()):
            return False
        if self.predicate.update_consensus(self):
            print "Saved Pair from being called too early"
            return False
        else:
            return True


    #@cached_property
    @property
    def consensus_location(self):
        return self._consensus_finder()


    def distribute_task(self):
        self.tasks_out += 1
        self.save(update_fields = ["tasks_out"])

    def collect_task(self):
        self.tasks_out -= 1
        self.predicate.add_total_task()
        self.save(update_fields = ["tasks_out"])

    def start(self):
        self.isStarted = True
        self.save(update_fields=["isStarted"])

    def reset(self):
        self.value=0
        self.num_yes=0
        self.num_no=0
        self.isDone=False
        self.status_votes=0
        self.inQueue=False
        self.save(update_fields=["value","num_yes","num_no","isDone","status_votes","inQueue"])

@python_2_unicode_compatible
class Task(models.Model):
    """
    Model representing one crowd worker task. (One HIT on Mechanical Turk.)
    """
    ip_pair = models.ForeignKey(IP_Pair, default=None)
    answer = models.NullBooleanField(default=None)
    workerID = models.CharField(db_index=True, max_length=15)

    #used for simulating task completion having DURATION
    start_time = models.IntegerField(default=0)
    end_time = models.IntegerField(default=0)

    # a text field for workers to give feedback on the task
    feedback = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return "Task from worker " + str(self.workerID) + " for IP Pair " + str(self.ip_pair)

@python_2_unicode_compatible
class DummyTask(models.Model):
    """
    Model representing a task that will be distributed that isn't associated w/ IP Pair
    """
    ip_pair = None
    answer = None
    workerID = models.CharField(db_index=True, max_length=15)

    start_time = models.IntegerField(default=0)
    end_time = models.IntegerField(default=0)

    def __str__(self):
        return "Placeholder task from worker " + str(self.workerID)
