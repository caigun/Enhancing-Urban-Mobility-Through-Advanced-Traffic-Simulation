from DataLoader import RoadMap
import pandas as pd
import numpy as np
import util


"""
Structure of nodes: nodes <- util.Counter(traffic lights)
nodes[any traffic light 1 with successor 2 3 4 5]: 
{
    policy: {2->1: time_interval[0, 20], 3->1: time_interval[20, 40], 4->1: time_interval[40, 60], 5->1: time_interval[60, 80]}
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

def initialize(nodes):
    """
    Return the intial state of traffic, including the number of cars on each Segment of roads.

    """
    pass

def update(nodes, updateTime, time):
    """
    Update the traffic every updateTime seconds.
    """
    updateQueues(nodes, updateTime, time)
    updateTimeLists(nodes, updateTime, time)
    pass

def assignPolicy(nodes):
    """
    Assign policy to each traffic light. 
    """
    pass

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

def createTran(nodes):
    """
    Create the transition funtion to each successor of every traffic light
    P(1->2),P(1->3),P(1->4),P(1->5),P(1->disappear)
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


if __name__ == '__main__':

    # total time
    time = 60*60
    updateTime = 1

    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df, 0.03)
    rdSegDis = rdSegmentDis(roads)

    state = initialize(rdSegDis)
    while time:
        time -= updateTime
        state = update(state, updateTime, time)

