from DataLoader import RoadMap
import pandas as pd
import numpy as np
import util
import matplotlib.pyplot as plt
import os

class Simulation():
    def __init__(self, roads, trafficLightPolicy, timeIntervalOfAddCar, carAddBaseOn_rdSegDis, distNumOfCarAdd, 
    carAddPosRandom, distCarSpeed, distNumCarPass, updateTime, totalTime, trafficLevels):
        self.roads = roads
        self.nodes = util.Counter()
        self.trafficLightPolicy = trafficLightPolicy
        self.timeIntervalOfAddCar = timeIntervalOfAddCar
        self.carAddBaseOn_rdSegDis = carAddBaseOn_rdSegDis
        self.distNumOfCarAdd = distNumOfCarAdd
        self.carAddPosRandom = carAddPosRandom
        self.distCarSpeed = distCarSpeed
        self.distNumCarPass = distNumCarPass
        self.updateTime = updateTime
        self.totalTime = totalTime
        self.trafficLevels = trafficLevels
        self._rdSegmentDis()

    def _rdSegmentDis(self):
        """
        This function returns distances between every two adjacent traffic lights.
        """
        dis = util.Counter()
        for nodes, road in self.roads.rdSegment.items():
            point1 = (nodes[0].longitude, nodes[0].latitude)
            point2 = (nodes[1].longitude, nodes[1].latitude)
            dis[(nodes[0],nodes[1])] = self.roads.l2Distance(point1,point2)*111194
            dis[(nodes[1],nodes[0])] = self.roads.l2Distance(point1,point2)*111194
        self.rdSegDis = dis
    
    def initialCars(self):
        """
        Return the intial state of traffic, including the number of cars on each Segment of roads.
        """
        for node in self.roads.nodes:
            self.nodes[node] = dict()
            self.nodes[node]["Queues"] = dict()
            successors = self.roads.getSuccessors(node)
            for succ in successors:
                self.nodes[node]["Queues"][(succ,node)] = []
    
    def assignPolicy(self):
        """
        Assign policy to each traffic light
        """
        for node in self.roads.nodes:
            self.nodes[node]["Policy"] = dict()
            successors = self.roads.getSuccessors(node)
            self.nodes[node]["Policy"]["timeIntervals"] = self.trafficLightPolicy.copy()
            self.nodes[node]["Policy"]["timeForOneIteration"] = sum(self.trafficLightPolicy[:len(successors)])
    
    def createTransfunc(self):
        """
        Create the transition funtion to each successor of every traffic light
        P(1->2),P(1->3),P(1->4),P(1->5),P(1->disappear)
        """
        for node in self.roads.nodes:
            self.nodes[node]["TransProb"] = util.Counter()
            successors = self.roads.getSuccessors(node)
            self.nodes[node]["TransProb"] = 1/(len(successors)+1)
            
    def startRecord(self):
        """
        Records for a road segement: (average waiting time, number of cars have passed the intersection)
        """
        for node in self.roads.nodes:
            self.nodes[node]["Records"] = dict()
            successors = self.roads.getSuccessors(node)
            for succ in successors:
                self.nodes[node]["Records"][(succ,node)] = (0,0)
    
    def initialization(self):
        self.initialCars()
        self.assignPolicy()
        self.createTransfunc()
        self.startRecord()

    def genRV(self, dist):
        if dist[0] == "constant":
            return dist[1][0]
        if dist[0] == "uniform":
            return np.random.uniform(low=dist[1][0], high=dist[1][1])
        if dist[0] == "geometric":
            return np.random.geometric(1/(1+dist[1][0])) + 1
        if dist[0] == "exponential":
            return np.random.exponential(scale=dist[1][0])
        if dist[0] == "normal":
            return max(np.random.normal(loc=dist[1][0], scale=dist[1][1]), 0)
        if dist[0] == "poisson":
            return np.random.poisson(lam=dist[1][0])
    
    def addCars(self, time):
        """
        Add cars to the system
        """
        if time%self.timeIntervalOfAddCar != 0:
            return
        for node in self.roads.nodes:
            successors = self.roads.getSuccessors(node)
            for succ in successors:
                if self.carAddBaseOn_rdSegDis:
                    num = int(self.genRV((self.distNumOfCarAdd[0], (self.distNumOfCarAdd[1][0]*self.rdSegDis[(succ, node)]/200,))))
                else:
                    num = self.genRV(self.distNumOfCarAdd)
                for _ in range(num):
                    if self.carAddPosRandom:
                        position = self.genRV(("uniform", (0, self.rdSegDis[(succ, node)])))
                    else:
                        position = 0
                    speed = self.genRV(self.distCarSpeed)
                    self.nodes[node]["Queues"][(succ,node)].append(time + position/speed)
                self.nodes[node]["Queues"][(succ,node)].sort()
    
    def updateQueues(self, time):
        """
        update the queues: pop cars that are out, push new cars in
        """
        for node in self.roads.nodes:
            successors = self.roads.getSuccessors(node)
            if len(successors) == 0:
                continue
            iterTime = time%self.nodes[node]["Policy"]["timeForOneIteration"]
            for i in range(len(successors)):
                if iterTime < sum(self.nodes[node]["Policy"]["timeIntervals"][:i+1]):
                    succ = list(successors)[i]
                    break
            numCarPass = self.genRV(self.distNumCarPass)
            carPass = self.nodes[node]["Queues"][(succ,node)][:numCarPass]
            self.nodes[node]["Queues"][(succ,node)] = self.nodes[node]["Queues"][(succ,node)][numCarPass:]
            for car in carPass:
                if car > time:
                    break
                record = self.nodes[node]["Records"][(succ,node)]
                self.nodes[node]["Records"][(succ,node)] = ((record[0]*record[1]+(time-car))/(record[1]+1), record[1]+1)
                u = np.random.uniform()
                index0 = int(u*len(successors)+1)
                if index0 == len(successors):
                    continue
                success = list(successors)[index0]
                speed = self.genRV(self.distCarSpeed)
                self.nodes[success]["Queues"][(node,success)].append(time+self.updateTime+self.rdSegDis[(node, success)]/speed)
                self.nodes[success]["Queues"][(node,success)].sort()

    def simu(self, time):
        self.addCars(time)
        self.updateQueues(time)

    def simulation(self):
        self.initialization()
        for time in range(0, self.totalTime, self.updateTime):
            self.simu(time+self.updateTime)

    def trafficLevel(self, hot):
        if hot < self.trafficLevels[0]:
            return 0
        if hot < self.trafficLevels[1]:
            return 1
        if hot < self.trafficLevels[2]:
            return 2
        if hot < self.trafficLevels[3]:
            return 3
        if hot < self.trafficLevels[4]:
            return 4
        return 5

    def drawTraffic(self):
        draw = util.Counter()
        for node in self.roads.nodes:
            successors = self.roads.getSuccessors(node)
            for succ in successors:
                hot = self.nodes[node]["Records"][(succ,node)][0]
                draw[(succ,node)] = self.trafficLevel(hot)
        self.roads.drawRoadsWithStress(stress=draw)
        # plt.show()
    
    def updatePolicy(self, alpha=2):
        """
        Update policy for traffic lights by previous result: averge waiting times
        alpha: learning rate
        """
        for node in self.roads.nodes:
            successors = self.roads.getSuccessors(node)
            if len(successors) <= 1:
                continue
            maxSucc = None
            minSucc = None
            max, min = 0, 1000000
            successors = list(successors)
            for i in range(len(successors)):
                if self.nodes[node]["Records"][(successors[i],node)][0] >= max:
                    max = self.nodes[node]["Records"][(successors[i],node)][0]
                    maxSucc = i
                if self.nodes[node]["Records"][(successors[i],node)][0] <= min:
                    min = self.nodes[node]["Records"][(successors[i],node)][0]
                    minSucc = i
            if self.nodes[node]["Policy"]["timeIntervals"][maxSucc] > 480:
                self.nodes[node]["Policy"]["timeIntervals"][maxSucc] = self.nodes[node]["Policy"]["timeIntervals"][maxSucc] + alpha*2
                self.nodes[node]["Policy"]["timeForOneIteration"] += alpha*2
            elif self.nodes[node]["Policy"]["timeIntervals"][maxSucc] > 240:
                self.nodes[node]["Policy"]["timeIntervals"][maxSucc] = self.nodes[node]["Policy"]["timeIntervals"][maxSucc] + alpha
                self.nodes[node]["Policy"]["timeForOneIteration"] += alpha
            if self.nodes[node]["Policy"]["timeIntervals"][minSucc] < 60:
                self.nodes[node]["Policy"]["timeIntervals"][minSucc] = self.nodes[node]["Policy"]["timeIntervals"][minSucc] - alpha*2
                self.nodes[node]["Policy"]["timeForOneIteration"] -= alpha*2
            elif self.nodes[node]["Policy"]["timeIntervals"][minSucc] < 120:
                self.nodes[node]["Policy"]["timeIntervals"][minSucc] = self.nodes[node]["Policy"]["timeIntervals"][minSucc] - alpha
                self.nodes[node]["Policy"]["timeForOneIteration"] -= alpha


if __name__ == '__main__':

    df = pd.read_csv("Traffic_Signals.csv")
    roads = RoadMap(df, 0.03)
    trafficLightPolicy = [20,]*8
    # traffic light green time for every adjacent road segment
    carAddBaseOn_rdSegDis = False
    # whether the addings of cars based on the length of a road segment
    timeIntervalOfAddCar = 60
    # Add cars every {timeIntervalOfAddCar} seconds
    distNumOfCarAdd = ("geometric", (4,))
    # the distribution of number of cars to add each time
    carAddPosRandom = True
    # whether the added car is randomly distributed on the road or just simply at the intersection
    distCarSpeed = ("normal", (6,1))
    # the distribution of the speed for cars
    distNumCarPass = ("poisson", (2,))
    # the distribtion of the number of cars in every {updateTime} seconds
    updateTime = 2
    # uodate our system every {updateTime} seconds
    totalTime = 60*60*1
    # the total time of our simulation system
    trafficLevels = [30,60,120,240,480]
    # trafficLevels = [t1,t2,t3,t4,t5]: the average waiting time in (0, t1] is viewed as low,
    # in [t1, t2] is viewed as light, in [t2, t3] is viewed as moderate
    # in [t3, t4] is viewed as heavy, in [t4, t5] is viewed as extra heavy
    # in [t5, +oo) is  :( 

    simulation = Simulation(roads, trafficLightPolicy, timeIntervalOfAddCar, carAddBaseOn_rdSegDis, distNumOfCarAdd, 
    carAddPosRandom, distCarSpeed, distNumCarPass, updateTime, totalTime, trafficLevels)

    folder_name = "figures"
    if not os.path.exists('./'+folder_name):
        os.mkdir(('./'+folder_name))

        simulation.simulation()
        plt.figure()
        simulation.drawTraffic()
        plt.savefig(folder_name + "//Figure1.png")
        plt.show()

    """If you want to try policy modification, use codes below"""
    # for i in range(10):
    #     simulation.simulation()
    #     simulation.updatePolicy()
    #     print(i+1)
    #     plt.figure()
    #     simulation.drawTraffic()
    #     plt.show()
    #     plt.savefig(folder_name + "//Figure{}.png".format(i+1))