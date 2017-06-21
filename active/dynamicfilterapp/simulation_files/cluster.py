import math
import numpy
from random import choice
from plotScript import multi_hist_gen, multi_line_graph_gen

class ClusterkD():
    """
    A clustering class for any number of dimensions. Should never be used itself
    If you want to use this class, create a specific subclass for a set number
    of dimensions. All that must be written yourself is a distance function and
    a graphing function
    """
    mL,pL=[],[]
    data = []

    def distance(self,mean,point):
        """
        Currrently just yells at you to write your own distance function...
        """
        #TODO write an any dimension distance calc... shouldn't be hard
        raise ValueError("You never set up the distance function properly")

    def kstep(self):
        """
        runs a single iterative "step" of the clustering process
        """
        if self.data==None:
            raise ValueError("You never supplied starting data.")
        self.pL=[[] for i in range(self.k)]
        for point in self.data:
            dL=[]
            for mean in self.mL:
                dL.append(self.distance(mean,point))
            index=dL.index(min(dL))
            self.pL[index].append(point)
        for i in range(self.k):
            if not self.pL[i]:
                print "badThings!"
            self.mL[i] = self.centroid(self.pL[i])
            numpy.mean(self.pL[i])

    def centroid(self,pointsList):
        raise ValueError("You never set up the Centroid function properly")

    def nksteps(self,n):
        """
        just runs kstep a given number of times
        """
        for i in range(n):
            self.kstep()

    def distMeans(self):
        """
        randomly places the cluster means around the space
        """
        #TODO consider better options than this one
        self.mL=[]
        for i in range(self.k):
            val = choice(self.data)
            while val in self.mL:
                val = choice(self.data)
            self.mL.append(val)
            print val

    def dataInit(self,data):
        """
        Sets up supplied data, the means lists and runns 300 iterative steps
        """
        self.data = data
        self.distMeans()
        self.nksteps(300)

    def addVal(self,i):
        """
        Adds a single data point to the set. Moves around means in response
        """
        if self.data==None:
            raise ValueError("You never supplied starting data.")
        self.data.append(i)
        self.kstep()

    def graph(self):
        raise ValueError("You never supplied a custom graphing method")

    def __init__(self,data=None,k=3):
        self.k = k
        if data != None:
            self.dataInit(data)

class Cluster1D(ClusterkD):

    def distance(self,mean,point):
        return abs(point - mean)

    def graph(self):
        leg = [len(l) for l in self.pL]
        multi_hist_gen(self.pL,leg,'clustering1dGraphGen.png')

    def centroid(self,pointsList):
        return numpy.mean(pointsList)


class Cluster2D(ClusterkD):

    def distance(self,mean,point):
        xd = mean[0]-point[0]
        yd = mean[1]-point[1]
        return math.sqrt(xd*xd+yd*yd)

    def graph(self):
        xL,yL,leg=[],[],[]
        for l in self.pL:
            leg.append(len(l))
            x,y=[],[]
            for point in l:
                x.append(point[0])
                y.append(point[1])
            xL.append(x)
            yL.append(y)
        multi_line_graph_gen(xL,yL,leg,'clustering2dGraphGen.png',scatter=True)

    def centroid(self,pointsList):
        x,y=[],[]
        for point in pointsList:
            x.append(point[0])
            y.append(point[1])
        return (numpy.mean(x),numpy.mean(y))
