# # Django tools
from django.db import models
from django.test import TestCase
from django.db.models import F
from django.db.models import Sum

# # What we wrote
from views_helpers import *
from .models import *
from synthesized_data import *
import toggles
from simulation_files.plotScript import *
from responseTimeDistribution import *
import graphGen

# # Python tools
import numpy as np
from random import randint, choice
import math
import sys
import io
import csv
import time
from copy import deepcopy
from scipy.special import btdtr
from scipy import stats

class Webtest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.q = Question(question_ID=1, question_text="Are you having a good day?")
        cls.q.save()
        cls.i1 = Item(item_ID=1, name="Wednesday", item_type=toggles.ITEM_TYPE)
        cls.i1.save()
        cls.p = Predicate(predicate_ID=1, question=cls.q)
        cls.p.save()
        cls.ip1 = IP_Pair(item = cls.i1, predicate = cls.p)
        cls.ip1.save()

    def test1(self):
        print cls.q
        print cls.i1
        print cls.p
        print cls.ip1