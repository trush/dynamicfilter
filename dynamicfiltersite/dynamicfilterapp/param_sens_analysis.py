# put names of files into an array
# each file should represent a batch of simulations for a value
# and for each file, we should get one point (average of tasks)
with open("test_results/eddy_selVSamb.csv", "r") as f:
    data = [row for row in csv.reader(f)]
    data = data[1:]

    data2 = []
    for i in range(len(data)):
        data2.append(data[i])

    # should get number of tasks in each simulation
    # get average number of tasks
    # put it in an array
    x1 = [float(row[0]) for row in data2]
    y1 = [float(row[3]) for row in data2]

    arrayX = [x1]
    arrayY = [y1]

    # loop through this three times
    for i in range(len(arrayX)):
        # sort the data
        reorder = sorted(range(len(arrayX[i])), key = lambda ii: arrayX[i][ii])
        arrayX[i] = [arrayX[i][ii] for ii in reorder]
        arrayY[i] = [arrayY[i][ii] for ii in reorder]

        # make the scatter plot
        plt.scatter(arrayX[i], arrayY[i], s=30, alpha=0.15, marker='o')

        # determine best fit line
        par = np.polyfit(arrayX[i], arrayY[i], 1, full=True)

        slope=par[0][0]
        intercept=par[0][1]
        xl = [min(arrayX[i]), max(arrayX[i])]
        yl = [slope*xx + intercept  for xx in xl]

        # coefficient of determination, plot text
        variance = np.var(arrayY[i])
        residuals = np.var([(slope*xx + intercept - yy)  for xx,yy in zip(arrayX[i],arrayY[i])])
        Rsqr = np.round(1-residuals/variance, decimals=2)
        plt.text(.9*max(arrayX[i])+.1*min(arrayX[i]),.9*max(arrayY[i])+.1*min(arrayY[i]),'$R^2 = %0.2f$'% Rsqr, fontsize=30)

        plt.xlabel("Entropy Values")
        plt.ylabel("Difference between Actual and Estimated Selectivities")

        plt.plot(xl, yl, '-r')
        
        # depending on index, write graph to file with certain name
        if i == 0:
            plt.savefig('test_results/eddy_selVSamb.png')
        elif i == 1:
            plt.savefig('test_results/eddy2_selVSamb.png')
        elif i == 2:
            plt.savefig('test_results/random_selVSamb.png')
        else: 
            plt.savefig('test_results/optimal_selVSamb.png')

        plt.clf()
        plt.cla()