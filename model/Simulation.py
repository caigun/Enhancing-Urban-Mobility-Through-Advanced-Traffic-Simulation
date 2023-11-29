from DataLoader import RoadMap
import pandas as pd
import numpy as np
import util
import matplotlib.pyplot as plt
import os
import gui
import random
import math
import time

class Simulation():
    def __init__(self, roads, trafficLightPolicy, timeIntervalOfAddCar, carAddBaseOn_rdSegDis, distNumOfCarAdd, 
    carAddPosRandom, timeIntervalOfDeleteCar, distNumOfCarDelete, distCarSpeed, distNumCarPass, updateTime, totalTime,
    trafficLevels, animation, patchTime):
        self.roads = roads
        self.nodes = util.Counter()
        self.trafficLightPolicy = trafficLightPolicy
        self.timeIntervalOfAddCar = timeIntervalOfAddCar
        self.carAddBaseOn_rdSegDis = carAddBaseOn_rdSegDis
        self.distNumOfCarAdd = distNumOfCarAdd
        self.carAddPosRandom = carAddPosRandom
        self.timeIntervalOfDeleteCar = timeIntervalOfDeleteCar
        self.distNumOfCarDelete = distNumOfCarDelete
        self.distCarSpeed = distCarSpeed
        self.distNumCarPass = distNumCarPass
        self.updateTime = updateTime
        self.totalTime = totalTime
        self.trafficLevels = trafficLevels
        self.animation = animation
        self.patchTime = patchTime
        self.totalCar = 0
        self.numNewCar = []
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
            try:
                self.nodes[node]["TransProb"] = 1/len(successors)
            except:
                pass
            
    def startRecord(self):
        """
        Records for a road segement: (average waiting time, number of cars have passed the intersection)
        """
        for node in self.roads.nodes:
            self.nodes[node]["Records"] = dict()
            successors = self.roads.getSuccessors(node)
            for succ in successors:
                self.nodes[node]["Records"][(succ,node)] = [0, []]
    
    def initialization(self):
        self.initialCars()
        self.systemTime=time.time()
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
            return max(np.random.normal(loc=dist[1][0], scale=dist[1][1]), 1)
        if dist[0] == "poisson":
            return np.random.poisson(lam=dist[1][0])
        if dist[0] == "time-varying-rate":
            """
            In this case, the time varying parameters is a list in the form of:
            [(t0, parameter0), (t1, parameter1), (t2, parameter2), ...]
            where t0, t1, t2, ... is the timestamps that the value will change
            and parameter0, parameter1, parameter2, ... is the new values
            t0 must be nonpositive.
            """
            for t,p in dist[1]:
                if self.time>=t:
                    return self.genRV(self, ["poisson", p])
            print("Runtime error: invalid time:", int(t), "is not a valid timestamp.")
        if dist[0] == "time-varying-rate-linear":
            """
            In this case, the time varying parameters is a list in the form of:
            [(t0, parameter0), (t1, parameter1), (t2, parameter2), ...]
            where t0, t1, t2, ... is the timestamps that the value will change
            and parameter0, parameter1, parameter2, ... is the new node values.
            t0 must be nonpositive.
            """
            i=0
            while True:
                t,p=dist[1][i]
                if self.time>=t:
                    if self.time==0:
                        return self.genRV(["poisson", (p,)])
                    else:
                        return self.genRV(["poisson", ((self.time-t)/(t-dist[1][i-1][0])*(p-dist[1][i-1][1]),)])
                i+=1
                if i==len(dist):
                    break
            print("Runtime error: invalid time:", int(t), "is not a valid timestamp.")
    
    def addCars(self, time):
        """
        Add cars to the system
        """
        if time%self.timeIntervalOfAddCar != 0:
            return
        prev=self.totalCar
        # j=0
        # for node in self.roads.nodes:
        #     for successor in self.roads.getSuccessors(node):
        #         j+=len(self.nodes[node]["Queues"][(successor,node)])
        # if prev!=j:
        #     print(prev,j)
        # self.totalCar = 0
        for node in self.roads.nodes:
            successors = self.roads.getSuccessors(node)
            for succ in successors:
                if self.carAddBaseOn_rdSegDis:
                    if self.distNumOfCarAdd[0]=="time-varying-rate":
                        """
                        In this case, the time varying parameters is a list in the form of:
                        [(t0, parameter0), (t1, parameter1), (t2, parameter2), ...]
                        where t0, t1, t2, ... is the timestamps that the value will change
                        and parameter0, parameter1, parameter2, ... is the new values
                        t0 must be nonpositive.
                        """
                        num=None
                        for t,p in self.distNumOfCarAdd[1]:
                            if self.time>=t:
                                num=self.genRV(["poisson", [p*math.log10(2.4+self.rdSegDis[(succ, node)]/500),]])
                        if num==None:print("Runtime error: invalid time:", int(t), "is not a valid timestamp.")
                    elif self.distNumOfCarAdd[0]=="time-varying-rate-linear":
                        """
                        In this case, the time varying parameters is a list in the form of:
                        [(t0, parameter0), (t1, parameter1), (t2, parameter2), ...]
                        where t0, t1, t2, ... is the timestamps that the value will change
                        and parameter0, parameter1, parameter2, ... is the new node values.
                        t0 must be nonpositive.
                        """
                        i=0
                        dist=self.distNumOfCarAdd
                        num=None
                        while True:
                            t,p=dist[1][i]
                            if t<self.time:
                                i+=1
                                continue
                            elif i==len(dist[1]):
                                print("Runtime error: invalid time:", int(t), "is not a valid timestamp.")
                                break
                            else:
                                if self.time==0:
                                    num=self.genRV(["poisson", [p*math.log10(2.4+self.rdSegDis[(succ, node)]/500),]])
                                else:
                                    num=self.genRV(["poisson", [((self.time-dist[1][i-1][0])/(t-dist[1][i-1][0])*(p-dist[1][i-1][1])+dist[1][i-1][1])*math.log10(2.4+self.rdSegDis[(succ, node)]/500),]])
                                break
                            
                    else:
                        num = int(self.genRV((self.distNumOfCarAdd[0], (self.distNumOfCarAdd[1][0]*math.log10(2.4+self.rdSegDis[(succ, node)]/500),))))
                else:
                    num = self.genRV(self.distNumOfCarAdd)
                self.totalCar+=num
                for _ in range(num):
                    if self.carAddPosRandom:
                        position = self.genRV(("uniform", (0, self.rdSegDis[(succ, node)])))
                    else:
                        position = 0
                    speed = max(self.genRV(self.distCarSpeed), 1)
                    self.nodes[node]["Queues"][(succ,node)].append(time + position/speed)
                self.nodes[node]["Queues"][(succ,node)].sort()
                # self.totalCar += len(self.nodes[node]["Queues"][(succ,node)])
        self.numNewCar.append(self.totalCar-prev)
        # self.distNumOfCarDelete
    
    def deleteCar(self, time):
        """
        delete car in the system
        """
        if time%self.timeIntervalOfDeleteCar != 0:
            return
        for node in self.roads.nodes:
            successors = self.roads.getSuccessors(node)
            for succ in successors:
                num = self.genRV(self.distNumOfCarAdd)
                self.totalCar-=num
                for _ in range(num):
                    length = len(self.nodes[node]["Queues"][(succ,node)])
                    if length == 0:
                        break
                    deleteindex = random.randint(0, length-1)
                    del self.nodes[node]["Queues"][(succ,node)][deleteindex]
    
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
                if random.random()<0.15:
                    self.totalCar-=1
                    continue
                # record = self.nodes[node]["Records"][(succ,node)]
                # self.nodes[node]["Records"][(succ,node)] = ((record[0]*record[1]+(time-car))/(record[1]+1), record[1]+1)
                self.nodes[node]["Records"][(succ,node)][1].append((time+self.updateTime, time-car))
                self.nodes[node]["Records"][(succ,node)][1] = [i for i in self.nodes[node]["Records"][(succ,node)][1] if time-i[0] <= 60*5]
                if len(self.nodes[node]["Records"][(succ,node)][1]) == 0:
                    self.nodes[node]["Records"][(succ,node)][0] = 0
                else:
                    X = [i[1] for i in self.nodes[node]["Records"][(succ,node)][1]]
                    self.nodes[node]["Records"][(succ,node)][0] = sum(X)/len(X)
                u = np.random.uniform()
                index0 = int(u*len(successors))
                success = list(successors)[index0]
                speed = self.genRV(self.distCarSpeed)
                self.nodes[success]["Queues"][(node,success)].append(time+self.updateTime+self.rdSegDis[(node, success)]/speed)
                self.nodes[success]["Queues"][(node,success)].sort()

    def simu(self, time):
        self.addCars(time)
        self.updateQueues(time)
        self.deleteCar(time)

    def simulation(self):
        self.initialization()
        if animation:
            self.patch=[]
            self.wtt=[]
        else:
            self.patch=None
            self.wtt=None
        self.time=0
        while self.time<self.totalTime:
            # print(self.totalCar)
            self.simu(self.time+self.updateTime)
            if animation:
                draw = util.Counter()
                waitingTime = util.Counter()
                for node in self.roads.nodes:
                    successors = self.roads.getSuccessors(node)
                    for succ in successors:
                        hot = self.nodes[node]["Records"][(succ,node)][0]
                        draw[(succ,node)] = self.trafficLevel(hot)
                        waitingTime[(succ,node)] = hot
                self.patch.append(draw)
                self.wtt.append(waitingTime)
            self.time+=self.updateTime
            if self.time%100==0:
                os.system('clear')
                print("=================================")
                print("Time: {:.1f} sec".format(time.time()-self.systemTime))
                print("Progress: {:.2f}%".format(self.time/self.totalTime*100))
                print("Iteration:", self.time, "/", self.totalTime)
                print("Avg waiting time: {:.2f}".format(sum(waitingTime.values())/len((waitingTime).values()),"(second)"))
                print("=================================")
        # print(self.totalCar)
        os.system('clear')
        print("=================================")
        print("Simulation Completed!")
        print("Time: {:.1f} sec".format(time.time()-self.systemTime))
        print("Iteration:", self.time, "/", self.totalTime)
        print("=================================")
        if animation:
            gui.run(self, False)
            pass

    def loadStressData(self):
        return self.patch

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
        self.roads.drawRoadsWithStress(stress=draw, wrtT=self.wtt, nca=self.numNewCar, withName=False)
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
    carAddBaseOn_rdSegDis = True
    # whether the addings of cars based on the length of a road segment
    timeIntervalOfAddCar = 30
    # Add cars every {timeIntervalOfAddCar} seconds
    # distNumOfCarAdd = ("time-varying-rate-linear", [(0,1),(3000,1.3),(4000,1.3), (7000, 1),(float('inf'),1.5)])
    distNumOfCarAdd = ("time-varying-rate-linear", [(0,0.5), (3600, 0.5), (5000,0.9), (10000, 0.9), (3*3600, 0.5),\
                                                    (3600*5, 0.8),(3600*5.5, 0.8), (3600*6, 0.5), (1000000, 0.5)])
    # distNumOfCarAdd = ("time-varying-rate-linear", [(0,0.5), (3000, 0.5), (6000,1), (9000, 1), (12000, 0), (1000000, 0.5)])
    # the distribution of number of cars to add each time on each road segment
    """
    pattern that you can choose from: time-varying-rate
    In this case, the time varying parameters is a list in the form of:
    [(t0, parameter0), (t1, parameter1), (t2, parameter2), ...]
    where t0, t1, t2, ... is the timestamps that the value will change
    and parameter0, parameter1, parameter2, ... is the new values
    t0 must be nonpositive.

    pattern that you can choose from: time-varying-rate-linear
    In this case, the time varying parameters is a list in the form of:
    [(t0, parameter0), (t1, parameter1), (t2, parameter2), ...]
    where t0, t1, t2, ... is the timestamps that the value will change
    and parameter0, parameter1, parameter2, ... is the new node values.
    t0 must be nonpositive.

    other pattern you can choose from: poisson, constant, uniform, geometric, exponential
    """
    carAddPosRandom = True
    # whether the added car is randomly distributed on the road or just simply at the intersection

    # ========== THIS PARAMETER IS NO LONGER IN USE ==========
    distNumOfCarDelete = ("poisson", (2,))
    # the distribution of number of cars to delete each time on each road segment
    timeIntervalOfDeleteCar = 2
    # Delete cars every {timeIntervalOfDeleteCar} seconds
    # ========================================================

    distCarSpeed = ("normal", (15,5))
    # the distribution of the speed for cars
    distNumCarPass = ("poisson", (1/2,))
    # the distribtion of the number of cars in every {updateTime} seconds
    updateTime = 2
    # uodate our system every {updateTime} seconds
    totalTime = 60*60*8
    # the total time of our simulation system
    trafficLevels = [30,50,70,90,120]
    # trafficLevels = [2,4,8,16,32]
    # trafficLevels = [t1,t2,t3,t4,t5]: the average waiting time in (0, t1] is viewed as low,
    # in [t1, t2] is viewed as light, in [t2, t3] is viewed as moderate
    # in [t3, t4] is viewed as heavy, in [t4, t5] is viewed as extra heavy
    # in [t5, +oo) is  :( 

    animation = True
    # whether use the animation for step by step update
    patchTime=60
    # the time for each gui update

    simulation = Simulation(roads, trafficLightPolicy, timeIntervalOfAddCar, carAddBaseOn_rdSegDis, distNumOfCarAdd, 
    carAddPosRandom, timeIntervalOfDeleteCar, distNumOfCarDelete, distCarSpeed, distNumCarPass, updateTime, totalTime, 
    trafficLevels, animation, patchTime)

    folder_name = "figures"
    if not os.path.exists('./'+folder_name):
        os.mkdir(('./'+folder_name))

    simulation.simulation()
    simulation.drawTraffic()
    # plt.savefig(folder_name + "//Figure1.png")

    """If you want to try policy modification, use codes below"""
    # for i in range(10):
    #     simulation.simulation()
    #     simulation.updatePolicy()
    #     print(i+1)
    #     plt.figure()
    #     simulation.drawTraffic()
    #     plt.show()
    #     plt.savefig(folder_name + "//Figure{}.png".format(i+1))