import pandas as pd
import matplotlib.pyplot as plt
import re
import util
import numpy as np
import math

def rightShift(pos1, pos2):
    """
    This function will compute the right-shift direction unit vector for the given
    vector in map,
    the vector in map is represented as pos1 --> pos2.

    e.g.
    (0,0) --> (1,0)
    the right-shift direction unit vector is
    (0,-1)

    (2,1) --> (3,2)
    the right-shift direction unit vector is
    (0.707, 0.707)
    """
    # calculate and normalize the given vector first
    vector=[pos2[0]-pos1[0], pos2[1]-pos1[1]]
    vector=[i/math.sqrt(vector[0]**2+vector[1]**2) for i in vector]
    x=vector[0]
    y=vector[1]

    # turn the direction 90 degree and return
    return (y, -x)


class lightNode():
    def __init__(self, latitude, longitude, cnn, streets=[], successors=set()):
        self.latitude=latitude
        self.longitude=longitude
        self.streets=streets
        self.successors=successors
        self.coo=(latitude,longitude)
        self.cnn=cnn

class RoadMap():
    """
    This is the main part defining the problem.

    ** When initializing the system, there is a parameter that is avalible to choose:

    lenTol: the tolerance level of the lenth between two ligths on the same street/road\\
    when this level is set to reletively high (or even inf, as default), the system may
    create strange roads (from a very far crossroad to another), since there may be no
    other traffic lights. This situation can be solved if all the crossroads (including
    those without traffic lights, or we can imagine that the traffic lights there is always
    green). However in this simplier model, we just do not consider the non-traffic lights
    crossroads.

    ** Useful parameters that you can retrived from this class:

    * df = all traffic lights data
    * lenTol = road lenth tolerance level
    * rdSegment = road Segments (note that this is a two-way segments dictionary, refer to
    _reconstructRoads for detailed usage)
    * nodes = all nodes in this system
    
    ** Useful functions:
    
    * drawLights(highlight=None) : draw all the lights in the map, if hightLight (a specific road
    name, string) is given, the map will highlight all the lights on this street/road.

    * findNode(cnn) : return a node with certain cnn

    * drawRoads(highlight=None) : draw all the roads (segments) that were identified by the system.
    if highlight is given, this function will only draw the highlight street/road. Note: this function
    is still improving. Please report if there is any bug. :)

    * getSuccessors(node) : return all the successors that can go from this light. Stored in array

    * drawRoadsWithStress(stress) : draw all the roads with a given traffic jam stress dictionary.

    * deleteRoadbyNode(node1, node2) &
      deleteRoadbyCNN(cnn1, cnn2) : delete a road connected by node 1 and node 2, reference by cnn
      or node.

    * addRoadbyNode(node1, node2, roadName) &
      addRoadbyCNN(cnn1, cnn2, roadName) : add a road connected by node 1 and node 2, reference by
      cnn or node, and this road segment belongs to road "roadName".
    """
    def __init__(self,df,lenTol=float('inf')):
        self.df=df.loc[:,("STREET1","STREET2","STREET3","shape","CNN")]
        self.lightNumber=len(df["STREET1"])
        self.lenTol=lenTol
        self._reconstructLights()
        self._reconstructNodes()
        self._reconstructRoads()
        self._modifyByConfig()
        self.scale=0.00005

    def _reconstructLights(self):
        lightLocation=self.df["shape"]
        pattern = r'POINT \((-?\d+\.\d+) (-?\d+\.\d+)\)'
        dtx=[]
        dty=[]
        for i in lightLocation:
            match = re.search(pattern, i)
            dtx.append(float(match.group(1)))
            dty.append(float(match.group(2)))
        self.df["dtx"]=dtx
        self.df["dty"]=dty
    
    def _modifyByConfig(self):
        with open("config.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            if line[0:3]=="***":
                continue
            data = line.strip().split(",")
            try:
                if data[2]=="a":
                    self.addRoadbyCNN(data[0], data[1])
                elif data[2]=="d":
                    self.deleteRoadbyCNN(data[0], data[1])
                else:
                    print("WARNING: Modifying road map exit with excetions:",\
                          data[0],"and", data[1], "are not valid CNN.")
                    break
            except:
                print("WARNING: Modifying road map exit with exceptions:",\
                      data[0],"and", data[1], "are not valid CNN that connect a road.")
                break

    def drawLights(self, highlight=None):
        plt.scatter(self.df["dtx"], self.df["dty"], s=5)
        if highlight:
            x=[]
            y=[]
            for i in self.roads[highlight]:
                y.append(i.latitude)
                x.append(i.longitude)
            plt.scatter(x,y,s=5,color='red')
        plt.show()

    def findNode(self, cnn):
        """
        Search and return the specific node by CNN number
        """
        for i in self.nodes:
            if i.cnn==cnn: return i

    def _reconstructNodes(self):
        """
        To find out every node(traffic light)'s successors(the next traffic lights for drivers who passes this node)
        according to the street/road information stored in self.df, and link the closest node of the same street/road
        to be the next node.

        Every nodes have these information:
        * node.streets = array containing all streets/roads the node in
        * node.successors = array containing all the neiboring nodes that are accessible from the current node
        * node.latitude = latitude of this node, i.e., df["dty"]
        * node.longitude = longitude of this node, i.e., df["dtx"]
        * node.coo = coordinate of this node

        The successor collecting process is done in self._reconstructRoads
        """
        self.nodes=[]
        self.roads=util.Counter()
        for index, row in self.df.iterrows():
            node=lightNode(row["dty"],row["dtx"],row["CNN"],successors=set())
            for i in [row["STREET1"],row["STREET2"],row["STREET3"]]:
                if i==i:
                    node.streets.append(i)
                    rd=self.roads[i]
                    if rd==0:self.roads[i]=[node]
                    else:self.roads[i].append(node)
            self.nodes.append(node)

    def l2Distance(self, point1, point2):
        return math.sqrt((point1[0]-point2[0])**2+(point1[1]-point2[1])**2)

    def _findClosestKPointandDistance(self, nodes:list, node:tuple):
        """
        Return the nodes that have distance to the specified node in increasing order,
        not containing the node itself
        """
        bank={}
        for i in nodes:
            bank[i]=self.l2Distance(node.coo,i.coo)
        sortedBank=sorted(bank.items(), key=lambda item: item[1])
        return [i for i in sortedBank[1:]]
    
    def _isReverseDirection(self, node, successor1, successor2):
        """
        To check whether the two closest successors are in the same direction(in this case, they are not likely
        to be both successors)
        """
        v1=(node.latitude-successor1.latitude, node.longitude-successor1.longitude)
        v2=(node.latitude-successor2.latitude, node.longitude-successor2.longitude)
        if v1[0]*v2[0]+v1[1]*v2[1]<=0:
            return True
        else:return False

    def _reconstructRoads(self):
        """
        Acoording to the nodes constructed with successors, link all the nodes with their successor(which is a street/road
        segment).

        Store the road data in terms of dictionary: key=set(node1, node2), value=road
        """
        self.rdSegment={}
        for road in self.roads.keys():
            nodes=self.roads[road]
            if len(nodes)==1:continue
            elif len(nodes)==2:
                if self.l2Distance(nodes[0].coo,nodes[1].coo)>self.lenTol:
                    continue
                nodes[0].successors.add(nodes[1])
                self.rdSegment[(nodes[1],nodes[0])]=road
                self.rdSegment[(nodes[0],nodes[1])]=road
                nodes[1].successors.add(nodes[0])
                continue
            for node in nodes:
                kPoint=self._findClosestKPointandDistance(nodes, node)
                successor1=kPoint[0][0]
                successor2=kPoint[1][0]
                if self._isReverseDirection(node, successor1, successor2):
                    if not kPoint[0][1]>self.lenTol:
                        node.successors.add(successor1)
                        successor1.successors.add(node)
                        self.rdSegment[(node,successor1)]=road
                        self.rdSegment[(successor1,node)]=road
                    if not kPoint[1][1]>self.lenTol:
                        node.successors.add(successor2)
                        successor2.successors.add(node)
                        self.rdSegment[(node,successor2)]=road
                        self.rdSegment[(successor2,node)]=road
                else:
                    if kPoint[0][1]>self.lenTol:
                        continue
                    node.successors.add(successor1)
                    successor1.successors.add(node)
                    self.rdSegment[(node,successor1)]=road
                    self.rdSegment[(successor1,node)]=road
                    for i in kPoint[2:]:
                        if i[1]>self.lenTol:break
                        if self._isReverseDirection(node, successor1, i[0]):
                            self.rdSegment[(node,i[0])]=road
                            self.rdSegment[(i[0],node)]=road
                            node.successors.add(i[0])
                            i[0].successors.add(node)
                            break

    def getSuccessors(self, node):
        return node.successors

    def drawRoads(self, highlight=None, withName=False):
        if withName:
            for node in self.nodes:
                x=node.longitude
                y=node.latitude
                plt.text(x,y,str(node.cnn))
        plt.show()
        if highlight!=None:
            for nodes, road in self.rdSegment.items():
                if road==highlight:
                    plt.plot([i.longitude for i in nodes],[i.latitude for i in nodes], color="RED")
                else:
                    plt.plot([i.longitude for i in nodes],[i.latitude for i in nodes], color=(110/256,130/256,230/256))
            return
        for nodes, rd in self.rdSegment.items():
            plt.plot([i.longitude for i in nodes],[i.latitude for i in nodes], color=(110/256,130/256,230/256))

    def drawRoadsWithStress(self, stress=util.Counter(), wrtT=False, nca=None):
        colorGradient=[(51/256,255/256,51/256), (153/256,255/256,51/256), (255/256,255/256,51/256),\
                       (255/256,153/256,51/256), (51/256,255/256,51/256), (255/256,51/256,51/256),\
                        (0,0,0)]
        for nodes, rd in self.rdSegment.items():
            n1, n2 = nodes
            l1, l2 = (n1.longitude, n1.latitude), (n2.longitude, n2.latitude)
            if l1==l2:
                continue
            direction=[i*self.scale for i in rightShift(l1,l2)]
            plt.plot([i.longitude+direction[0] for i in nodes],[i.latitude+direction[1] for i in nodes], color=colorGradient[int(stress[nodes])])
        plt.show()

        if wrtT and nca:
            stress=[]
            var=[]
            for stress_data in wrtT:
                stress.append(sum(stress_data.values())/len(stress_data.values()))
                var.append(np.std(list(stress_data.values())))
            t=[2*i/60 for i in range(len(stress))]
            # plt.plot(t, stress)

            fig, ax1 = plt.subplots()

            color = 'tab:red'
            ax1.set_xlabel('time (min)')
            ax1.set_ylabel('avg waiting time (s)', color=color)
            ax1.plot(t, stress, color=color)
            ax1.tick_params(axis='y', labelcolor=color)

            ax2 = ax1.twinx()

            color = 'tab:blue'
            ax2.set_ylabel('Number of joining cars', color=color)
            ax2.plot([i/2 for i in range(len(nca))], nca, color=color)
            ax2.tick_params(axis='y', labelcolor=color)
            fig.tight_layout()

            # plt.fill_between(t, [stress[i]-var[i] for i in range(len(stress))],\
            #                 [stress[i]+var[i] for i in range(len(stress))], alpha=0.5, edgecolor='#CC4F1B', facecolor='#FF9848')
            # plt.xlabel("t /min")
            # plt.ylabel("Overall stress /level")
            plt.show()

    def deleteRoadbyNode(self, node1:lightNode, node2:lightNode):
        """
        Delete a specific road connected node 1 and node 2
        """
        self.rdSegment[(node1, node2)]=None
        self.rdSegment[(node2, node1)]=None
        del(node1.successors, node2)    # need to verify the usage
        del(node2.successors, node1)

    def deleteRoadbyCNN(self, cnn1, cnn2):
        self.deleteRoadbyNode(self.findNode(cnn1), self.findNode(cnn2))

    def addRoadbyNode(self, node1:lightNode, node2:lightNode, roadName:str):
        self.rdSegment[(node1, node2)]=roadName
        self.rdSegment[(node2, node1)]=roadName
        node1.successors.add(node2)
        node2.successors.add(node1)

    def addRoadbyCNN(self, cnn1, cnn2, roadName:str):
        self.addRoadbyNode(self.findNode(cnn1), self.findNode(cnn2), roadName)


if __name__ == '__main__':
    """
    For testing only
    """
    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df, 0.03)



    f = plt.figure()
    f.set_figwidth(10)
    f.set_figheight(6)
    roads.drawRoads(withName=True)
    # roads.drawRoadsWithStress()
    # roads.drawLights("VALENCIA")
    # roads.drawRoads()
    # plt.show()