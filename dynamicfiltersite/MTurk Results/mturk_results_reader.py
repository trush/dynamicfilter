import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

filename = sys.argv[1]

A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,AA,AB,AC,AD,AE,AF,AG,AH,AI = np.genfromtxt(filename, skiprows=1,
	delimiter=',',
	dtype={'names': ('HITId',
		             'HITTypeId',
		             'Title',
		             'Description',
		             'Keywords',
		             'Reward',
		             'CreationTime',
		             'MaxAssignments',
		             'RequesterAnnotation',
		             'AssignmentDurationInSeconds',
		             'AutoApprovalDelayInSeconds',
		             'Expiration',
		             'NumberOfSimilarHITs',
		             'LifetimeInSeconds',
		             'AssignmentId',
		             'WorkerId',
		             'AssignmentStatus',
		             'AcceptTime',
		             'SubmitTime',
		             'AutoApprovalTime',
		             'ApprovalTime',
		             'RejectionTime',
		             'RequesterFeedback',
		             'WorkTimeInSeconds',
		             'LifetimeApprovalRate',
		             'Last30DaysApprovalRate',
		             'Last7DaysApprovalRate',
		             'Input.Restaurant',
		             'Input.Address',
		             'Input.Question',
		             'Answer.MultiLineTextInput',
		             'Answer.Q1AnswerPart1',
		             'Answer.box1',
		             'Approve',
		             'Reject'
                    ),
			'formats':('U30', # HITId
				       'U30', # HITTypeId
				       'U34', # Title
				       'U104', # Description
				       'U16', # Keywords
				       'U5', # Reward
				       'U28', # CreationTime
				       'i4', # MaxAssignments
				       'U16', # RequesterAnnotation
				       'i4',
				       'i4',
				       'U28',
				       'i4',
				       'i4',
				       'U32',
				       'U14',
				       'U15',
				       'U28', # Accept/Submit/AutoApproval Times
				       'U28',
				       'U28',
				       'U28', # Approval/Rejection Times
				       'U28',
				       'U50', # Requester feedback
				       'i4', # Work time (s)
				       'U20', # Approval Rates
				       'U20',
				       'U20',
				       'U20', # Input.Restaurant
				       'U40', # Input.Address
				       'U50', # Input.Question
				       'U100', # Answer.MultiLineTextInput
				       'i4', # Answer.Q1AnswerPart1
				       'U14', # Answer.box1
				       'U5', # Approve
				       'U5' # Reject
					   )
          })
comments = filter(lambda x: x!={}, AE)
print comments