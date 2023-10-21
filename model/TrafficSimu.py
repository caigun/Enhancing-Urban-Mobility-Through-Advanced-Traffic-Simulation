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

def initialCars(nodes, roads, rdSegDis, divisor):
    """
    Return the intial state of traffic, including the number of cars on each Segment of roads.
    """
    for node in roads.nodes:
        nodes[node] = dict()
        nodes[node]["Queues"] = dict()
        successors = roads.getSuccessors(node)
        for succ in successors:
            nodes[node]["Queues"][(succ,node)] = [0] * int(rdSegDis[(succ,node)]/divisor)

def assignPolicy(nodes, roads, timePolicy):
    """
    Assign policy to each traffic light.
    """
    for node in roads.nodes:
        nodes[node]["Policy"] = dict()
        successors = list(roads.getSuccessors(node))
        timeIntervals = []
        for i in range(len(successors)):
            timeIntervals.append((successors[i],timePolicy[i]))
        nodes[node]["Policy"]["timeIntervals"] = timeIntervals
        nodes[node]["Policy"]["timeForOneIteration"] = sum(timePolicy[:len(successors)])

def createTrans(nodes, roads, transPolicy):
    """
    Create the transition funtion to each successor of every traffic light
    P(1->2),P(1->3),P(1->4),P(1->5),P(1->disappear)
    """
    if transPolicy == None:
        for node in roads.nodes:
            nodes[node]["Policy"] = util.Counter()
            successors = roads.getSuccessors(node)
            nodes[node]["TransProb"] = 1/(len(successors)+1)
    else:
        pass

def initialize(nodes, roads, rdSegDis, divisor=50, timePolicy=[20,]*6, transPolicy = None):
    initialCars(nodes, roads, rdSegDis, divisor)
    assignPolicy(nodes, roads, timePolicy)
    createTrans(nodes, roads, transPolicy)

# def updatePolicy(nodes, results, alpha):
#     """
#     Update policy for traffic lights by previous result: averge waiting times
#     alpha: learning rate
#     """
#     pass

def addCars(nodes):
    """
    Add cars to the traffic.
    """
    pass
    
def updateQueues(nodes, updateTime, time, distPassingTime):
    """
    update the queues: pop cars that are out, push new cars in
    """

    pass

def updateTimeLists(nodes, updateTime, time):
    """
    update the time lists for recording time of cars to pass the intersection
    """
    pass

def update(nodes, updateTime, time, distPassingTime="constant"):
    """
    Update the traffic every updateTime seconds.
    """
    updateQueues(nodes, updateTime, time, distPassingTime)
    updateTimeLists(nodes, updateTime, time)
    addCars(nodes)
    pass


if __name__ == '__main__':

    time = 60*60                        # total time
    updateTime = 1                      # update every updateTime seconds
    avgCarPassingTime = 5               # average time for a car to pass the intersection
    distPassingTime = "constant"             # distribution of car passing time, "exp", "constant", "xxx"

    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df, 0.03)
    rdSegDis = rdSegmentDis(roads)

    nodes = util.Counter()
    initialize(nodes, roads, rdSegDis, divisor=50, timePolicy=[20,]*6, transPolicy = None)
    
    while time:
        time -= updateTime
        update(nodes, updateTime, time)

