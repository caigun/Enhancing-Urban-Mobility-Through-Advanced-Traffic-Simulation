from DataLoader import RoadMap
import pandas as pd
import numpy as np
import util


def rdSegmentDis(roads):
    """
    This function returns distances between every two adjacent traffic lights.
    """
    dis = util.Counter()
    for nodes, road in roads.rdSegment.items():
        point1 = (nodes[0].longitude, nodes[0].latitude)
        point2 = (nodes[1].longitude, nodes[1].latitude)
        dis[nodes] = roads.l2Distance(point1,point2)*111194
    return dis

def initialize(rdSegDis, divisor=20):
    """
    Return the intial state of traffic, including the number of cars on each Segment of roads.
    """
    initial = rdSegDis.divideAll(divisor)
    return initial

def update(state, updateTime):
    """
    Update the traffic every updateTime seconds.
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
        state = update(state, updateTime)

    # print(rdSegDis) 
    print(state)
