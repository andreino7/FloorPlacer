__author__ = 'Filippo'



from gurobipy import *
import traceback
import sys
import hashlib
import time

#whether to generates computing intensive WL cuts
USE_2REG_WL_CUT = False


"""
This method solves the floorplanning problem using a MILP
model based on the conflict graph of the intersection
relationship between regions

@param problem The problem data (see exampleProblem.py for an example)
@param fpgaData The fpga data (see the json files in fpga folder)
@param relocation Wheter to optimize the problem using the relocation metrics or not
@param fixedRegions a pre-defined solution for the problem

@return a dictionary containing the solution data
"""


def solve(prob, fpgaData, relocation, fixedRegions):
    problem=prob
    result = {'status': False}
    startTime = time.time()
    #-----------------------------------------------------------
    # parameters setup
    #-----------------------------------------------------------

    #parse the fpga data
    fpga = {
        'maxX' : fpgaData['maxTX'],
        'maxY' : fpgaData['maxTY'],
        'tileW' : fpgaData['tileW'],
        'tileH' : fpgaData['tileH'],
        'matrix' : fpgaData['matrix']
    }
    fpga['resources'] = [res for res in fpgaData['resources']]
    resPerType = {res:fpgaData['resources'][res]['number'] for res in fpgaData['resources']}

    #fpga['resources'] += ['NULL','-F-']
    resPerType['NULL'] = 0
    resPerType['-F-'] = 1
    problem['res_cost']['NULL'] = 0
    problem['res_cost']['-F-'] = 0
    problem['res_cost']['NonRec'] = 0


    #parse the problem data
    #problem['obj_weights']['WL'] = problem['obj_weights']['wirelength']
    problem['obj_weights']['P'] = problem['obj_weights']['perimeter']
    problem['obj_weights']['R'] = problem['obj_weights']['resources']
    problem['obj_weights']['B'] = problem['obj_weights']['bitstream']

    problem['regions'] = [r for r in problem['regions_data']]
    problem['regRes'] = {}

    for regName in problem['regions_data']:
        region = problem['regions_data'][regName]
        for resName in region['resources']:
            res = region['resources'][resName]
            problem['regRes'][(regName,resName)] = int(res)
            # problem['regRes'][(rec3,CLB)]=920

    problem['io'] = {}
    for regName in problem['regions_data']:
        region = problem['regions_data'][regName]
        problem['io'][regName] = []
        for io in region['io']:
            problem['io'][regName].append((io['tileX'],io['tileY'],io['wires']))






    #generate the fpga resource matrix
    matrix = {}

    for t in fpga['resources']:
        for x in xrange(0,fpga['maxX']):
            for y in xrange(0,fpga['maxY']):
                matrix[x,y,t]=0


    lengths = {}
    for b in fpga['matrix']:
        matrix[b['x'],b['y'],b['t']]= b['l']*b['d']
        lengths[b['x'],b['y']] = b['l']
    #computes the resources on each column
    colRes = {}

    try:
        for x in xrange(0,fpga['maxX']):
            for t in fpga['resources']:
                colRes[x,0,t] = matrix[x,0,t]
                for y in xrange(1,fpga['maxY']):
                    colRes[x,y,t] = colRes[x,y-1,t] + matrix[x,y,t]
    except:
        print "The set of portions is not a partitioning of the fpga!";
        traceback.print_exc()
        return


    #computes the resources from the bottom-left corner to a specific coordinate
    blRes = {}

    for t in fpga['resources']:
        for y in xrange(0,fpga['maxY']):
            blRes[0,y,t] = colRes[0,y,t]
            for x in xrange(1,fpga['maxX']):
                blRes[x,y,t] = blRes[x-1,y,t] + colRes[x,y,t]

    #boundary conditions to simplify resource computations:
    for t in fpga['resources']:
        blRes[-1,-1,t] = 0
        for y in xrange(0,fpga['maxY']):
            blRes[-1,y,t] = 0
        for x in xrange(0,fpga['maxX']):
            blRes[x,-1,t] = 0



    #function for the computation of resources within an area
    #example: areaRes((x1,y1,x2,y2),'CLB')
    areaRes = lambda area, t: blRes[area[2],area[3],t] + blRes[area[0]-1,area[1]-1,t] - blRes[area[2],area[1]-1,t] - blRes[area[0]-1,area[3],t]

    #computes the upper bounds on the objective function metrics

    # max resource waste
    Rmax = 0
    for t in fpga['resources']:
        Rmax += areaRes((0,0,fpga['maxX']-1,fpga['maxY']-1), t)#*problem['res_cost'][t]
        for r in problem['regions']:
            if (r,t) in problem['regRes']:
                Rmax -= problem['regRes'][(r,t)]#*problem['res_cost'][t]

    # max perimeter
    Pmax = len(problem['regions'])*(fpga['maxY']*fpga['tileH'] + fpga['maxX']*fpga['tileW'])*2



    c=0

    for t in range (fpga['maxX']):
        c+=lengths[t,0]

    BMax =c*2


    def isFeasibile(r,area):
        wastedRes = {}
        for t in fpga['resources']:
            wastedRes[t] = areaRes(area,t)

            if (r,t) in problem['regRes'].keys():
                wastedRes[t] -= problem['regRes'][r,t]
                if wastedRes[t] < 0:
                    return False
        return True

    # select the area placement generation strategy
    isDominated = None

    placementStrategy = problem['placement_generation_mode']
    if placementStrategy == 'width-reduced':
        isDominated = lambda r,x1,y1,x2,y2: isFeasibile(r,(x1,y1+1,x2,y2))
    elif placementStrategy == 'irreducible':
        isDominated = lambda r,x1,y1,x2,y2: isFeasibile(r,(x1+1,y1,x2,y2)) or isFeasibile(r,(x1,y1+1,x2,y2)) or isFeasibile(r,(x1,y1,x2,y2-1)) or isFeasibile(r,(x1,y1,x2-1,y2))
    elif placementStrategy == 'all':
        isDominated = lambda r,x1,y1,x2,y2: False

    print 'got here'
    #-----------------------------------------------------------
    # variables and constraints generation
    #-----------------------------------------------------------

    areas = tuplelist()
    clusters = tuplelist()
    numAreasForRegion = {}
    areaSize = {}
    areasXSquare = {}
    areasXColumn ={}
    areasXCluster = {}
    areasIOCost = {}
    areasRCost = {}
    areasPCost = {}
    areasBCost={}
    areasCXCost = {}
    areasCYCost = {}
    areasMinCCost = {}
    minWLComm = {}
    minWLComm2 = {}
    minWLCommX = {}
    minWLCommX2 = {}
    minWLCommY = {}
    minWLCommY2 = {}

    import multiprocessing

    class placerthread(multiprocessing.Process):
        global problem
        global fpga
        def __init__(self, threadID, name, reg,q):
            multiprocessing.Process.__init__(self)
            self.threadID = threadID
            self.name = name
            self.reg = reg
            self.res=[]
            self.q=q
        def run(self):
            print "Starting " + self.name
            findPossibleAreas(self.reg,self.q)
            #self.q.put(self.res)
            print "Exiting " + self.name

        def getRes(self):
            return self.res

        def getReg(self):
            return self.reg




    def findPossibleAreas(r,queue):
        numAreasForRegion = {}
        areaSize = {}
        areasXSquare = {}
        areasXColumn ={}
        areasXCluster = {}
        areasIOCost = {}
        areasRCost = {}
        areasPCost = {}
        areasBCost={}
        areasCXCost = {}
        areasCYCost = {}
        areasMinCCost = {}

        areas = []
        x1Min = 0
        x1Max = fpga['maxX']
        y1Min = 0
        y1Max = fpga['maxY']
        x2Min = lambda x1: x1
        x2Max = fpga['maxX']
        y2Min = lambda y1: y1
        y2Max = lambda y1: fpga['maxY']

        # IMPORTANT: this version of the algorithm generates irreducible rectangles
        for x1 in xrange(x1Min, x1Max):
            for y1 in xrange(y1Min, y1Max):
                lastX=fpga['maxX']
                for y2 in xrange(y2Min(y1), y2Max(y1)):
                    for x2 in xrange(x2Min(x1), lastX):

                        #verify that the resource requirements are met
                        satisfied = True
                        forbidden = False
                        wastedRes = {};

                        for t in fpga['resources']:
                            wastedRes[t] = areaRes((x1,y1,x2,y2),t)
                            if (r,t) in problem['regRes'].keys():
                                wastedRes[t] -= problem['regRes'][r,t]

                                if wastedRes[t] < 0:
                                    satisfied = False;
                                    break;

                        if forbidden:
                            break

                        if satisfied:

                            # verify that the area is not dominated
                            if isDominated(r,x1,y1,x2,y2):
                                break
                            a = (r,x1,y1,x2,y2)
                            queue.put(a)
                            lastX=x2
                            break;


    if fixedRegions == None:
        fixedRegions = {}

    for x in xrange(0, fpga['maxX']):
        areasXColumn[x] =  tuplelist()
        for y in xrange(0, fpga['maxY']):
            areasXSquare[x,y] = tuplelist()

    startRec= time.time()
    q=[]
    i=0
    t=[]
    for r in problem['regions']:
        numAreasForRegion[r] = 0
        q.append(multiprocessing.Queue())
        t.append(placerthread(i,"Th"+str(i),r,q[-1]))
        t[-1].start()
        i+=1

    # let the processes start


    while (any(jj.is_alive() for jj in t)):
        for iii,jjj in enumerate(t):
            if not q[iii].empty():
                areas+=[q[iii].get()]


    for proc in t:
        proc.join()

    for iii,jjj in enumerate(t):
            if not q[iii].empty():
                areas+=[q[iii].get()]



    print("Time spent generating areas: ", time.time() - startRec)
    startRec= time.time()

    for a in areas:
        # insert the area as a possible solution for the region

        r,x1,y1,x2,y2 = a
        areaSize[a] = (x2-x1+1)*(y2-y1+1)
        numAreasForRegion[r] = numAreasForRegion[r] + 1
        # update areasXSquare dict
        # bigger in order to separate the regions( Altera )
        for x in xrange(x1, min(x2 + 2,fpga['maxX'])):
            areasXColumn[x] += [a]
            for y in xrange(y1, min(y2 + 2,fpga['maxY'])):
                areasXSquare[x,y] += [a]



        #computes area cost
        cost = 0
        for tp in fpga['resources']:
            cost = cost + areaRes((x1,y1,x2,y2),tp)#*problem['res_cost'][t]
        areasRCost[a] = cost

        #computes Bitstream cost
        c = 0
        for tp in range(x1,x2+1):
            c+=lengths[tp,y1]

        areasBCost[a] = c
        #print len(areas)
        #computes perimeter cost
        areasPCost[a] = (x2-x1+1) + (y2-y1+1)






    # verifies that each region has at least a feasible placement
    for r in problem['regions']:
        if numAreasForRegion[r] == 0:
            # no valid solution can exists
            return "Unfeasible"

    print("Time spent Union areas: ", time.time() - startRec)
    def overlapping(a1,a2):
        wtot = a1[3] + a2[3] - a1[1] - a2[1]
        htot = a1[4] + a2[4] - a1[2] - a2[2]
        wcur = max(a1[3],a2[3]) - min(a1[1],a2[1])
        hcur = max(a1[4],a2[4]) - min(a1[2],a2[2])
        return wcur <= wtot and hcur <= htot




    print 'Areas: ' + str(len(areas))
    axql = 0
    for x in xrange(0, fpga['maxX']):
        for y in xrange(0, fpga['maxY']):
            axql += len(areasXSquare[x,y])
    print 'Non overlapping terms: ' + str(axql)
    print 'Clusters: ' + str(len(areasXCluster))


    # define variable
    #colVar={}
    areaVars = {}
    ANDORandAreaVars = {}
    centroidXVars = {}
    centroidYVars = {}
    commXVars = {}
    commYVars = {}

    clusterVars = {}
    m = Model("floorplan")


    #for c in range(fpga['maxX']):
     #   colVar[c] = m.addVar(0.0,1.0,0.0,GRB.BINARY,"ColUsed"+str(c))

    for a in areas:
        areaVars[a] = m.addVar(0.0,1.0,0.0,GRB.BINARY, str(a))
        ANDORandAreaVars[a] = m.addVar(0.0,1.0,0.0,GRB.BINARY, "ANDOR ^ Area"+str(a))

    for r in problem['regions']:
        centroidXVars[r] = m.addVar(0.0,GRB.INFINITY,0.0,GRB.CONTINUOUS, 'centroid_x_' + str(r))
        centroidYVars[r] = m.addVar(0.0,GRB.INFINITY,0.0,GRB.CONTINUOUS, 'centroid_y_' + str(r))

    #IOCost = m.addVar(0.0, GRB.INFINITY, float(problem['obj_weights']['WL'])/WLmax, GRB.CONTINUOUS, 'IOCost')
    RCost = m.addVar(0.0, GRB.INFINITY, float(problem['obj_weights']['R'])/Rmax, GRB.CONTINUOUS, 'RCost')
    PCost = m.addVar(0.0, GRB.INFINITY, float(problem['obj_weights']['P'])/Pmax, GRB.CONTINUOUS, 'PCost')
    ANDORVar = m.addVar(0.0,1.0,0.0,GRB.BINARY, "ANDOR Usage")
    BCost = m.addVar(0.0,GRB.INFINITY,float(problem['obj_weights']['B'])/BMax, GRB.CONTINUOUS, 'BCost')
    ANDORCost = m.addVar(0.0,GRB.INFINITY,float(problem['obj_weights']['B'])/BMax, GRB.CONTINUOUS, 'ANDORCost')


    m.update()


    # define constraints


    # no overlapping between regions
    for y in xrange(0, fpga['maxY']):
        for x in xrange(0, fpga['maxX']):
            if(len(areasXSquare[x,y]) > 0):
                m.addConstr(quicksum(areaVars[a] for a in areasXSquare[x,y]) <= 1, 'noOverlapping_' + str(x) + '_' + str(y))

    #ALTERA ONLY
    # If vertical overlap then ANDOR Mode
    for x in xrange(0, fpga['maxX']):
        if (len(areasXColumn[x])>0):
            m.addConstr(quicksum(areaVars[a] for a in areasXColumn[x])<= 1 + (ANDORVar * len(areasXColumn[x])), "ANDORConstraint"+str(x) )
    #ALTERA
    # Creates binary variable representing ANDOR and AreaVar
    s=0
    for a in areas:
        s+=1
        m.addConstr(ANDORandAreaVars[a]<=areaVars[a],"first_binDef"+str(s) )
        m.addConstr(ANDORandAreaVars[a]<=ANDORVar,"second_binDef"+str(s) )
        m.addConstr(ANDORandAreaVars[a]>=areaVars[a]+ANDORVar-1,"third_binDef"+str(s) )


    #ALTERA ONLY
    # Used Columns definition
    #for x in xrange(0, fpga['maxX']):
     #       m.addConstr(quicksum(areaVars[a] for a in areasXColumn[x])<= colVar[x]*len(areasXColumn[x]), "COLUsageDef"+str(x))



    # one area for region
    for r in problem['regions']:
        m.addConstr(quicksum(areaVars[a] for a in areas.select(r,'*','*','*','*')) == 1, 'oneAndOnlyOne_'+str(r))

    #ALTERA ONLY
    # Bitstream Computation
    m.addConstr(quicksum(areaVars[a]*areasBCost[a] for a in areas) == BCost, 'BCost_def')
    m.addConstr(quicksum(ANDORandAreaVars[a] * areasBCost[a] for a in areas) == ANDORCost, 'ANDORCost_def')


    # wasted resources computation
    m.addConstr(quicksum(areaVars[a]*areasRCost[a] for a in areas) == RCost, 'RCost_def')

    # perimeter computation
    m.addConstr(quicksum(areaVars[a]*areasPCost[a] for a in areas) == PCost, 'PCost_def')


    # io computation
    #m.addConstr(quicksum(areaVars[a]*areasIOCost[a] for a in areas) == IOCost, 'IOCost_def')


    m.modelSense = GRB.MINIMIZE


    for paramName in problem['gurobi_params']:
        value = problem['gurobi_params'][paramName]
        m.setParam(paramName, value)

    m.optimize()

    endTime = time.time()
    deltaTime = round((endTime-startTime)*1000) / 1000.0

    print ''
    print '---> total time: ' + str(deltaTime)
    print ''

    result['time'] = deltaTime

    if(m.getAttr('solCount') > 0):
        print('#### solution fuond ####')

        result['status'] = True
        result['objective'] = m.getAttr('ObjVal')

        if not relocation:
            result['metrics'] = {
            'absolute' : {
            #'wirelength' : IOCost.getAttr('X'),
            'perimeter' : PCost.getAttr('X'),
            'resources' : RCost.getAttr('X'),
            'ANDORCost' :  ANDORCost.getAttr('X'),
            'BCost' : BCost.getAttr('X'),
            'ANDOR' : ANDORVar.getAttr('X'),
            'BMAX' : BMax
            },
            'relative' : {
            #'wirelength' : ( IOCost.getAttr('X')) / WLmax ,
            'perimeter' : PCost.getAttr('X') / Pmax,
            'resources' : RCost.getAttr('X') / Rmax,
            'Bitstream' : (BCost.getAttr('X')+ ANDORCost.getAttr('X'))/ BMax,

            }


            }

        result['regions'] = {}

        index = 1
        if relocation:
            for a in areas:
                val = areaVars[a].getAttr('X')
                if val > 0.1:
                    info = eval(areaVars[a].getAttr('VarName'))
                    result['regions'][info[0] + '_' + str(index)] = {
                    'x1' : info[1],
                    'y1' : info[2],
                    'x2' : info[3],
                    'y2' : info[4]
                    }
                    index = index + 1
        else:
            for a in areas:
                val = areaVars[a].getAttr('X')
                if val > 0.1:
                    info = eval(areaVars[a].getAttr('VarName'))
                    result['regions'][info[0]] = {
                    'x1' : info[1],
                    'y1' : info[2],
                    'x2' : info[3],
                    'y2' : info[4]
                    }


    else:
        print('#### infeasible ####')
        return "Unfeasible"

    return result