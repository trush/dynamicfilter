import csv
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

DEBUG = False

def makeCSV(data):
    ''' Writes a 4 by n 2D list to a CSV file called join_data.csv '''
    download_dir = "join_data.csv" #where you want the file to be downloaded to 
    csv = open(download_dir, "w") #"w" indicates that you're writing strings to the file

    columnTitleRow = "Pairs processed, Cost of Adaptive Algorithm, Cost of PJF Join, Cost of PW Join\n"
    csv.write(columnTitleRow)

    for iteration in range(len(data)):
        pair = data[0][iteration]
        cost_AA = data[1][iteration]
        cost_PFJ = data[2][iteration]
        cost_PW = data[3][iteration]
        row = str(pair) + "," + str(cost_AA) + "," + str(cost_PFJ) + "," + str(cost_PW) + "\n"
        csv.write(row)

def makeJoinCostPlot(data):
    '''Make a plot of 3 lines given a 4 by n 2D list. Used to plot graphs of join costs '''
    ### PLOT COSTS ###
    plt.plot(data[0], data[1],'r--', label='Adaptive Algorithm Average Cost')
    plt.plot(data[0], data[2], 'b--', label ='PJF Join Average Cost')
    plt.plot(data[0], data[3], 'g--', label= 'PW Join Average Cost')

    ### ADJUST AXES AND LEGEND ###
    max_y = max( [max(data[1]),max(data[2]),max(data[3])] )
    min_y = min( [min(data[1],min(data[2],min(data[3])))] )
    plt.ylim(ymin=min_y*0.9,ymax=max_y*1.1) # TODO:need to automate this assignment
    plt.legend()
    plt.xlabel('Pairs Processed')
    plt.ylabel('Cost (time units)')

    ### DEBUGGING ###
    if DEBUG:
        print "ABOUT GRAPH ---------"
        print "max and min y values: " + str(max_y) + ", " + str(min_y)
        print "---------------------"
        
    fig = plt.gcf()
    ### SHOW AND SAVE ###
    plt.show()
    fig.savefig('Cost of Various Join algorithms.png')
    
data = [[1,2,3,4],[60,55,53,50],[60,60,50,50],[50,50,50,50]]
makeCSV(data)
makeJoinCostPlot(data)