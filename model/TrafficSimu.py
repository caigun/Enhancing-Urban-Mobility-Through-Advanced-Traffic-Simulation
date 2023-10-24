from DataLoader import RoadMap
import pandas as pd
import numpy as np
import util


"""
Structure of nodes: nodes <- util.Counter(traffic lights)
nodes[any traffic light 1 with successor 2 3 4 5]: 
{
    Policy: {timeIntervals:[(2->1,time=20),(3->1,time=20),(4->1,time=20),(5->1,time=20)], timeForOneIteration:80}
    Queues: {queue of 2->1: [Times for cars to be at intersection], queue of 3->1: [Times for cars to be in intersection],...}
    Transition probability: 1/(# of successor + 1(disappear))
    Records: (mean, number)
}
"""
def rdSegmentDis(roads):
    """
    This function returns distances between every two adjacent traffic lights.
    """
    dis = util.Counter()
    for nodes, road in roads.rdSegment.items():
        point1 = (nodes[0].longitude, nodes[0].latitude)
        point2 = (nodes[1].longitude, nodes[1].latitude)
        dis[(nodes[0],nodes[1])] = roads.l2Distance(point1,point2)*111194
        dis[(nodes[1],nodes[0])] = roads.l2Distance(point1,point2)*111194
    return dis

def genPassingTime(distPassingTime):
    if distPassingTime[0] == "constant":
        return distPassingTime[1]
    if distPassingTime[0] == "exponential":
        return np.random.exponential(scale=1/distPassingTime[1],size=1)
    if distPassingTime[0] == "normal":
        return np.random.normal(loc=distPassingTime[1][0], scale=distPassingTime[1][1])

def initialCars(nodes, roads, rdSegDis, divisor, distPassingTime):
    """
    Return the intial state of traffic, including the number of cars on each Segment of roads.
    """
    for node in roads.nodes:
        nodes[node] = dict()
        nodes[node]["Queues"] = dict()
        successors = roads.getSuccessors(node)
        for succ in successors:
            nodes[node]["Queues"][(succ,node)] = [0 for _ in range(int(rdSegDis[(succ,node)]/divisor))]

def assignPolicy(nodes, roads, timePolicy):
    """
    Assign policy to each traffic light.
    """
    for node in roads.nodes:
        nodes[node]["Policy"] = dict()
        successors = roads.getSuccessors(node)
        # timeIntervals = []
        # for i in range(len(successors)):
        #     timeIntervals.append((successors[i],timePolicy[i]))
        # nodes[node]["Policy"]["timeIntervals"] = timeIntervals
        nodes[node]["Policy"]["timeIntervals"] = timePolicy
        nodes[node]["Policy"]["timeForOneIteration"] = sum(timePolicy[:len(successors)])

def createTrans(nodes, roads, transPolicy):
    """
    Create the transition funtion to each successor of every traffic light
    P(1->2),P(1->3),P(1->4),P(1->5),P(1->disappear)
    """
    if transPolicy == None:
        for node in roads.nodes:
            nodes[node]["TransProb"] = util.Counter()
            successors = roads.getSuccessors(node)
            nodes[node]["TransProb"] = 1/(len(successors)+1)
    else:
        pass

def startRecord(nodes, roads):
    for node in roads.nodes:
        nodes[node]["Records"] = dict()
        successors = roads.getSuccessors(node)
        for succ in successors:
            nodes[node]["Records"][(succ,node)] = (0,0)

def initialize(nodes, roads, rdSegDis, divisor, distPassingTime, timePolicy, transPolicy):
    initialCars(nodes, roads, rdSegDis, divisor, distPassingTime)
    assignPolicy(nodes, roads, timePolicy)
    createTrans(nodes, roads, transPolicy)
    startRecord(nodes, roads)

# def updatePolicy(nodes, results, alpha):
#     """
#     Update policy for traffic lights by previous result: averge waiting times
#     alpha: learning rate
#     """
#     pass

def addCars(nodes, roads, divisor, time, rdSegDis, distPassingTime):
    """
    Add cars to the traffic.
    """
    if time%20 != 0:
        return
    for node in roads.nodes:
        successors = roads.getSuccessors(node)
        for succ in successors:
            for _ in range(int(rdSegDis[(succ,node)]/divisor)):
                nodes[node]["Queues"][(succ,node)].append(time)
    
def updateQueues(nodes, updateTime, time, distPassingTime, rdSegDis, speed):
    """
    update the queues: pop cars that are out, push new cars in
    """
    for node in roads.nodes:
        successors = roads.getSuccessors(node)
        if len(successors) == 0:
            continue
        iterTime = time%nodes[node]["Policy"]["timeForOneIteration"]
        for i in range(len(successors)):
            if iterTime < sum(nodes[node]["Policy"]["timeIntervals"][:i+1]):
                succ = list(successors)[i]
                break
        # numCarPass = np.random.geometric(p=0.5,size=1)
        numCarPass = int(updateTime/2)
        carPass = nodes[node]["Queues"][(succ,node)][:numCarPass]
        nodes[node]["Queues"][(succ,node)] = nodes[node]["Queues"][(succ,node)][numCarPass:]
        for car in carPass:
            if car > time:
                break
            record = nodes[node]["Records"][(succ,node)]
            nodes[node]["Records"][(succ,node)] = ((record[0]*record[1]+(time-car))/(record[1]+1), record[1]+1)
            u = np.random.uniform()
            index0 = int(u*len(successors)+1)
            if index0 == len(successors):
                continue
            success = list(successors)[index0]
            # print(roads.getSuccessors(success),success)
            # print(roads.getSuccessors(node),node)
            # print(node.cnn,success.cnn)
            # print(time)
            try:
                nodes[success]["Queues"][(node,success)].append(time+updateTime+rdSegDis[(node, success)]/speed)
            except:
                pass

def update(nodes, roads, updateTime, time, rdSegDis, distPassingTime, divisor=100, speed=10):
    """
    Update the traffic every updateTime seconds.
    """
    updateQueues(nodes, updateTime, time, distPassingTime, rdSegDis, speed)
    addCars(nodes, roads, divisor, time, rdSegDis, distPassingTime)

if __name__ == '__main__':

    time = 60*50                        # total time in second
    updateTime = 2                      # update every updateTime seconds
    avgCarPassingTime = 5               # average time for a car to pass the intersection
    distPassingTime = ("constant",5)      
    # distribution of car passing time, ("exponential",5), ("constant",5), ("normal",(5,2))

    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df, 0.03)
    rdSegDis = rdSegmentDis(roads)

    nodes = util.Counter()
    initialize(nodes, roads, rdSegDis, divisor=50, distPassingTime=distPassingTime, timePolicy=[20,]*6, transPolicy = None)

    t = 0
    while t<time:
        t += updateTime
        update(nodes, roads, updateTime, t, rdSegDis, distPassingTime, divisor=100, speed=10)
        print("time: {} complete".format(t))
    
    for node in roads.nodes:
        successors = roads.getSuccessors(node)
        for succ in successors:
            print(nodes[node]["Records"][(succ,node)])

