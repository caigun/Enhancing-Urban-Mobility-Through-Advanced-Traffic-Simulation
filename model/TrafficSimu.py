from DataLoader import RoadMap
import pandas as pd
import numpy as np
import util


"""
Structure of nodes: nodes <- util.Counter(traffic lights)
nodes[any traffic light 1 with successor 2 3 4 5]: 
{
    Policy: {2->1: time_interval[0, 20], 3->1: time_interval[20, 40], 4->1: time_interval[40, 60], 5->1: time_interval[60, 80]}
    Queues: {queue of 2->1: [Times for cars to be at intersection], queue of 3->1: [Times for cars to be in intersection],...}
    Transition function:{2:P(1->2), 3:P(1->3),..., disappear:P(disappear)}
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

def initialCars(nodes, roads, rdSegDis, divisor=50):
    """
    Return the intial state of traffic, including the number of cars on each Segment of roads.
    """
    for node in roads.nodes:
        nodes[node] = dict()
        nodes[node]["Queues"] = dict()
        successors = roads.getSuccessors(node)
        for succ in successors:
            nodes[node]["Queues"][(succ,node)] = [0] * (rdSegDis[(succ,node)]//divisor)

def assignPolicy(nodes, roads, timePolicy=[0,20,40,60,80]):
    """
    Assign policy to each traffic light.
    """
    for node in roads.nodes:
        nodes[node]["Policy"] = dict()
        successors = roads.getSuccessors(node)
        for i in range(len(successors)):
            nodes[node]["Policy"][(successors[i],node)] = [timePolicy[i],timePolicy[i+1]]

def createTrans(nodes, roads, transProb = None):
    """
    Create the transition funtion to each successor of every traffic light
    P(1->2),P(1->3),P(1->4),P(1->5),P(1->disappear)
    """
    if transProb == None:
        for node in roads.nodes:
            nodes[node]["Policy"] = util.Counter()
            successors = roads.getSuccessors(node)
            l = len(successors)
            for succ in successors:
                nodes[node]["Policy"][(node,succ)] = 1/l
    else:
        pass

def initialize(nodes, roads, rdSegDis, divisor=50, timePolicy=[0,20,40,60,80], transProb = None):
    initialCars(nodes, roads, rdSegDis, divisor=50)
    assignPolicy(nodes, roads, timePolicy=[0,20,40,60,80])
    createTrans(nodes, roads, transProb = None)

def updatePolicy(nodes, results, alpha):
    """
    Update policy for traffic lights by previous result: averge waiting times
    alpha: learning rate
    """
    pass

def addCars(nodes):
    """
    Add cars to the traffic.
    """
    pass
    
def updateQueues(nodes, updateTime, time):
    """
    update the queues: pop cars that are out, push new cars in
    """
    pass

def updateTimeLists(nodes, updateTime, time):
    """
    update the time lists.
    """
    pass

def update(nodes, updateTime, time):
    """
    Update the traffic every updateTime seconds.
    """
    updateQueues(nodes, updateTime, time)
    updateTimeLists(nodes, updateTime, time)
    pass


if __name__ == '__main__':

    time = 60*60                        # total time
    updateTime = 1                      # update every updateTime seconds
    avgCarPassingTime = 5               # average time for a car to pass the intersection
    # distPassingTime = "exp"             # distribution of car passing time

    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df, 0.03)
    rdSegDis = rdSegmentDis(roads)

    nodes = util.Counter()
    initialize(nodes, roads, rdSegDis, divisor=50, timePolicy=[0,20,40,60,80], transProb = None)
    
    while time:
        time -= updateTime
        update(nodes, updateTime, time)

