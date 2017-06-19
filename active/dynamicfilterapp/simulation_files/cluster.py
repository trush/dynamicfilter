
import numpy
from random import choice
from plotScript import multi_hist_gen
class Cluster():
    k=3
    mL,pL=[],[]
    data = []
    def kstep(self):
        self.pL=[[] for i in range(self.k)]
        for point in self.data:
            dL=[]
            for mean in self.mL:
                dL.append(abs(point-mean))
            index=dL.index(min(dL))
            self.pL[index].append(point)
        for i in range(self.k):
            if not self.pL[i]:
                print "badThings!"
            self.mL[i] = numpy.mean(self.pL[i])
    def nksteps(self,n):
        for i in range(n):
            self.kstep()
    def distMeans(self):
        self.mL=[]
        for i in range(self.k):
            val = choice(self.data)
            while val in self.mL:
                val = choice(self.data)
            self.mL.append(val)
    def dataInit(self,data):
        self.data = data
        self.distMeans()
        self.nksteps(300)
    def addVal(self,i):
        self.data.append(i)
        if len(self.data)%20 == 0:
            self.nksteps(20)
        else:
            self.nksteps(3)
    def graph(self):
        print self.pL
        multi_hist_gen(self.pL,['1','2','3'],'graphgen.png')
